"""Private, atomic profile revisions; no executor authority or secret-store access.

The per-profile state.sqlite is shared with future task/memory tables. SQLite is
canonical for these snapshots; file editing/IPC must stage bytes through apply().
No imported file is executed. Same-UID hostile code is outside this boundary.
"""
from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path
import re
import sqlite3
import stat
import time

try:
    from .protocol import strict_json
except ImportError:
    from protocol import strict_json


class ProfileError(ValueError):
    pass


class UnsupportedSchema(ProfileError):
    pass


def _identifier(value):
    if not isinstance(value, str) or not re.fullmatch(r'[a-z][a-z0-9-]{0,63}', value):
        raise ProfileError('invalid_profile_id')
    return value


def _schema(value, rule, field='config'):
    """Offline evaluator for exactly the keywords used by the bundled v1 schema.

    Reject unknown validation keywords rather than silently ignoring a future
    schema contract. Annotation keywords do not participate in validation.
    """
    supported = {'type', 'const', 'enum', 'required', 'properties',
                 'additionalProperties', 'minLength', 'maxLength', 'pattern',
                 'minimum', 'maximum', 'maxItems', 'uniqueItems', 'items',
                 'not', 'if', 'then', 'allOf', '$schema', 'title'}
    if set(rule) - supported:
        raise UnsupportedSchema('unsupported_profile_schema')
    types = {'object': lambda x: isinstance(x, dict),
             'array': lambda x: isinstance(x, list),
             'string': lambda x: isinstance(x, str), 'null': lambda x: x is None,
             'integer': lambda x: type(x) is int, 'boolean': lambda x: type(x) is bool}
    if 'type' in rule:
        names = rule['type'] if isinstance(rule['type'], list) else [rule['type']]
        if any(name not in types for name in names) or not any(types[name](value) for name in names):
            raise ProfileError('invalid_field:' + field)
    if 'const' in rule and (type(value) is not type(rule['const']) or value != rule['const']):
        raise ProfileError('invalid_field:' + field)
    if 'enum' in rule and not any(type(value) is type(item) and value == item for item in rule['enum']):
        raise ProfileError('invalid_field:' + field)
    if isinstance(value, dict):
        if set(rule.get('required', [])) - set(value):
            raise ProfileError('missing_field:' + field)
        properties = rule.get('properties', {})
        if rule.get('additionalProperties') is False and set(value) - set(properties):
            raise ProfileError('unknown_field:' + field)
        for key, item in value.items():
            if key in properties:
                _schema(item, properties[key], field + '.' + key)
    if isinstance(value, str):
        if len(value) < rule.get('minLength', 0) or len(value) > rule.get('maxLength', len(value)):
            raise ProfileError('invalid_field:' + field)
        if 'pattern' in rule and not re.search(rule['pattern'], value):
            raise ProfileError('invalid_field:' + field)
    if type(value) is int and not rule.get('minimum', value) <= value <= rule.get('maximum', value):
        raise ProfileError('invalid_field:' + field)
    if isinstance(value, list):
        if len(value) > rule.get('maxItems', len(value)):
            raise ProfileError('invalid_field:' + field)
        if rule.get('uniqueItems') and len({json.dumps(v, sort_keys=True) for v in value}) != len(value):
            raise ProfileError('invalid_field:' + field)
        if 'items' in rule:
            for item in value:
                _schema(item, rule['items'], field + '[]')
    if 'not' in rule:
        try:
            _schema(value, rule['not'], field)
        except UnsupportedSchema:
            raise
        except ProfileError:
            pass
        else:
            raise ProfileError('invalid_field:' + field)
    for sub in rule.get('allOf', []):
        _schema(value, sub, field)
    if 'if' in rule:
        try:
            _schema(value, rule['if'], field)
        except UnsupportedSchema:
            raise
        except ProfileError:
            pass
        else:
            _schema(value, rule.get('then', {}), field)


class ProfileStore:
    """One per-profile private store, with bounded immutable revision snapshots.

    capabilities is supplied by trusted installed-component discovery, never by
    profile JSON. It maps adapters/tools/skills/extensions/workflows to ID sets.
    connection IDs are opaque references; their actual ownership/resolution is
    checked by the broker before provider dispatch, independently of this store.
    """
    def __init__(self, directory, profile_id, schema, *, capabilities=None, clock=time.time,
                 revision_limit=11, byte_limit=16 * 1024 * 1024):
        self.profile_id = _identifier(profile_id)
        self.directory = Path(directory)
        self.schema = schema
        self.clock = clock
        self.capabilities = capabilities or {'adapters': set(), 'tools': {'system-info'},
                                           'skills': {'explain-system'}, 'extensions': set(),
                                           'workflows': set()}
        self.revision_limit = revision_limit
        self.byte_limit = byte_limit
        if (not self.directory.is_absolute() or self.directory.resolve() != self.directory
                or self.revision_limit < 2 or self.byte_limit < 65536):
            raise ProfileError('unsafe_profile_store')
        self.directory.mkdir(mode=0o700, exist_ok=True)
        info = self.directory.stat()
        if info.st_uid != os.getuid() or stat.S_IMODE(info.st_mode) != 0o700:
            raise ProfileError('unsafe_profile_store')
        self.path = self.directory / 'state.sqlite'
        fd = os.open(self.path, os.O_RDWR | os.O_CREAT | os.O_CLOEXEC | os.O_NOFOLLOW, 0o600)
        try:
            info = os.fstat(fd)
            if (not stat.S_ISREG(info.st_mode) or info.st_nlink != 1 or
                    info.st_uid != os.getuid() or stat.S_IMODE(info.st_mode) != 0o600):
                raise ProfileError('unsafe_profile_database')
        finally:
            os.close(fd)
        with self._db() as db:
            db.executescript('''
                CREATE TABLE IF NOT EXISTS profile_revisions(
                    revision TEXT PRIMARY KEY, bundle TEXT NOT NULL, size INTEGER NOT NULL,
                    created REAL NOT NULL);
                CREATE TABLE IF NOT EXISTS profile_current(
                    id INTEGER PRIMARY KEY CHECK(id=1),profile_id TEXT NOT NULL,
                    revision TEXT NOT NULL REFERENCES profile_revisions(revision));
                CREATE TABLE IF NOT EXISTS task_profiles(
                    task_id TEXT PRIMARY KEY, profile_id TEXT NOT NULL,
                    revision TEXT NOT NULL REFERENCES profile_revisions(revision),
                    created REAL NOT NULL);
            ''')
            row = db.execute('SELECT profile_id FROM profile_current WHERE id=1').fetchone()
            if row and row['profile_id'] != self.profile_id:
                raise ProfileError('profile_store_identity_conflict')

    @contextmanager
    def _db(self):
        db = sqlite3.connect(self.path, isolation_level=None, timeout=5)
        db.row_factory = sqlite3.Row
        db.execute('PRAGMA foreign_keys=ON')
        db.execute('PRAGMA synchronous=FULL')
        try:
            yield db
        finally:
            db.close()

    @contextmanager
    def _transaction(self):
        with self._db() as db:
            db.execute('BEGIN IMMEDIATE')
            try:
                yield db
                db.execute('COMMIT')
            except BaseException:
                db.execute('ROLLBACK')
                raise

    def validate(self, files):
        """Validate explicit bytes only; filesystem/archive traversal is not accepted.

        First slice supports config and four persona documents. Skill/workflow
        bodies remain installed separately, cannot be imported through this API.
        """
        allowed = {'config.json', 'SOUL.md', 'IDENTITY.md', 'USER.md', 'AGENTS.md'}
        if not isinstance(files, dict) or 'config.json' not in files or set(files) - allowed:
            raise ProfileError('unsupported_profile_path')
        bundle = {}
        for name, data in files.items():
            limit = 65536 if name == 'config.json' else 32768
            if type(data) is not bytes or len(data) > limit:
                raise ProfileError('profile_file_limit')
            try:
                bundle[name] = data.decode('utf-8', errors='strict')
            except UnicodeError:
                raise ProfileError('invalid_profile_utf8') from None
        try:
            config = strict_json(files['config.json'])
        except (ValueError, UnicodeError, RecursionError, OverflowError):
            raise ProfileError('invalid_profile_json') from None
        _schema(config, self.schema)
        if config['profile_id'] != self.profile_id:
            raise ProfileError('profile_identity_conflict')
        for group, ids in [('tools', config['tools']['enabled']),
                           ('skills', config['skills']['enabled']),
                           ('extensions', config['extensions']['enabled']),
                           ('workflows', config['automation']['workflow_ids'])]:
            if set(ids) - set(self.capabilities.get(group, ())):
                raise ProfileError('unavailable_' + group)
        provider = config['provider']
        if provider['mode'] != 'deferred':
            if provider['adapter_id'] not in self.capabilities.get('adapters', ()):
                raise ProfileError('unavailable_adapter')
            # Current pinned Pi/provider path has stricter measured runtime
            # bounds than the generic v1 schema. Invalid activation preserves
            # the working revision rather than failing only on next dispatch.
            if config['budgets']['max_tool_calls'] > 32 or config['budgets']['max_retries'] != 0:
                raise ProfileError('unsupported_provider_budget')
            if provider['adapter_id'] == 'local-llama-cpp':
                if provider['mode'] != 'local' or config['budgets']['max_context_tokens'] > 4096 or config['budgets']['max_output_tokens'] > 1024:
                    raise ProfileError('unsupported_local_profile')
            elif provider['mode'] == 'local' and provider['adapter_id'] in {'openai', 'openrouter', 'anthropic', 'openai-compatible'}:
                raise ProfileError('incompatible_provider_mode')
            if not re.fullmatch(r'[a-zA-Z0-9_-]{1,80}', provider['connection_ref']):
                raise ProfileError('invalid_connection_reference')
        manifest = {name: hashlib.sha256(files[name]).hexdigest() for name in sorted(files)}
        revision = hashlib.sha256(json.dumps(manifest, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
        encoded = json.dumps(bundle, sort_keys=True, ensure_ascii=False, separators=(',', ':'))
        return revision, encoded, config

    @staticmethod
    def _current(db):
        row = db.execute('SELECT revision FROM profile_current WHERE id=1').fetchone()
        return row['revision'] if row else None

    def current(self):
        with self._db() as db:
            return self._current(db)

    def apply(self, files, *, expected_revision):
        with self._transaction() as db:
            return self.apply_in_transaction(db, files, expected_revision=expected_revision)

    def apply_in_transaction(self, db, files, *, expected_revision):
        """Apply with canonical memory/projection changes in the same transaction.

        Trusted broker callers supply this store's existing SQLite transaction;
        this helper never commits it or weakens semantic/revision storage checks.
        """
        if not db.in_transaction:
            raise ProfileError('profile_transaction_required')
        databases = db.execute('PRAGMA database_list').fetchall()
        if not any(row[1] == 'main' and row[2] == str(self.path) for row in databases):
            raise ProfileError('profile_transaction_database_mismatch')
        revision, bundle, _ = self.validate(files)
        size = len(bundle.encode())
        if self._current(db) != expected_revision:
            raise ProfileError('stale_profile_revision')
        if db.execute('SELECT 1 FROM profile_revisions WHERE revision=?', (revision,)).fetchone() is None:
            # Never silently discard a prior revision or task-pinned snapshot.
            row = db.execute('SELECT count(*) AS n,coalesce(sum(size),0) AS bytes FROM profile_revisions').fetchone()
            if row['n'] >= self.revision_limit or row['bytes'] + size > self.byte_limit:
                raise ProfileError('profile_revision_storage_full')
            db.execute('INSERT INTO profile_revisions VALUES(?,?,?,?)',
                       (revision, bundle, size, self.clock()))
        db.execute('INSERT OR REPLACE INTO profile_current VALUES(1,?,?)', (self.profile_id, revision))
        return revision

    def snapshot(self, revision=None):
        with self._db() as db:
            return self.snapshot_in_transaction(db, revision)

    def snapshot_in_transaction(self, db, revision=None):
        """Read/revalidate immutable bytes on the caller's canonical connection."""
        databases = db.execute('PRAGMA database_list').fetchall()
        if not any(row[1] == 'main' and row[2] == str(self.path) for row in databases):
            raise ProfileError('profile_transaction_database_mismatch')
        revision = revision or self._current(db)
        row = db.execute('SELECT bundle FROM profile_revisions WHERE revision=?', (revision,)).fetchone()
        if row is None:
            raise ProfileError('unknown_profile_revision')
        try:
            files = {name: value.encode('utf-8') for name, value in strict_json(row['bundle'].encode()).items()}
            actual, _, _ = self.validate(files)
        except (ValueError, AttributeError, TypeError):
            raise ProfileError('profile_revision_corrupt') from None
        if actual != revision:
            raise ProfileError('profile_revision_corrupt')
        return files

    def restore(self, revision, *, expected_revision):
        # Revalidate original bytes against current availability before activation.
        return self.apply(self.snapshot(revision), expected_revision=expected_revision)

    def pin_task(self, task_id, *, expected_revision):
        """Atomic pin only; must precede dispatch. Idempotent, rejects changed pins."""
        if not isinstance(task_id, str) or not re.fullmatch(r'[a-zA-Z0-9_-]{1,128}', task_id):
            raise ProfileError('invalid_task_id')
        # Verify exact bytes before recording. Immutable snapshots are never deleted.
        self.snapshot(expected_revision)
        with self._transaction() as db:
            old = db.execute('SELECT revision FROM task_profiles WHERE task_id=?', (task_id,)).fetchone()
            if old:
                if old['revision'] != expected_revision:
                    raise ProfileError('task_profile_identity_conflict')
                return old['revision']
            if self._current(db) != expected_revision:
                raise ProfileError('stale_profile_revision')
            db.execute('INSERT INTO task_profiles VALUES(?,?,?,?)',
                       (task_id, self.profile_id, expected_revision, self.clock()))
        return expected_revision

    def task_snapshot(self, task_id):
        with self._db() as db:
            row = db.execute('SELECT revision FROM task_profiles WHERE task_id=?', (task_id,)).fetchone()
            if row is None:
                raise ProfileError('unknown_task_profile')
        return row['revision'], self.snapshot(row['revision'])

    def settings(self):
        revision = self.current()
        files = self.snapshot(revision)
        with self._db() as db:
            previous = [row['revision'] for row in db.execute(
                'SELECT revision FROM profile_revisions WHERE revision!=? ORDER BY created DESC,rowid DESC LIMIT 32', (revision,))]
        return {'version': 1, 'profile_revision': revision,
                'config': strict_json(files['config.json']), 'previous_revisions': previous}

    def recovery_snapshot(self):
        """Explicit read-only fallback; no activation, task replay or provider use.

        Recovery disables all tools, skills, automation/extensions and routing. It
        must be shown for owner review before any separate activation.
        """
        with self._db() as db:
            revisions = [row['revision'] for row in db.execute('SELECT revision FROM profile_revisions ORDER BY created DESC,rowid DESC')]
        for revision in revisions:
            try:
                files = self.snapshot(revision)
            except ProfileError:
                continue
            config = strict_json(files['config.json'])
            config['provider'] = {'mode': 'deferred', 'adapter_id': None, 'model_id': None,
                                  'connection_ref': None, 'allow_remote_fallback': False}
            config['budgets']['remote_spending_enabled'] = False
            for group in ('tools', 'skills', 'extensions'):
                config[group]['enabled'] = []
            config['automation'] = {'enabled': False, 'workflow_ids': []}
            files['config.json'] = json.dumps(config, sort_keys=True).encode()
            self.validate(files)
            return {'source_revision': revision, 'recovery_required': True, 'files': files}
        raise ProfileError('no_valid_profile_revision')
