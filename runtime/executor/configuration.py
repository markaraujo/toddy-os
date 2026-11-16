"""Qualified non-secret desired configuration with durable, no-replay rollback.

The authenticated root executor supplies operation IDs and the fixed registry.
Caller/model input never selects paths, schemas, backup directories or callbacks.
The initial registry is a disabled qualification consumer, not a control listener.
Existing unrestricted owner administration remains a separate explicit policy path.
"""
from contextlib import contextmanager
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import secrets
import shutil
import sqlite3
import stat
import time


MAX_CONFIG = 1024
DEFAULT_REGISTRY = {'managed-preview': Path('/etc/toddy/managed/preview-service.json')}


class ConfigurationError(ValueError):
    pass


def identifier(value):
    if not isinstance(value, str) or not re.fullmatch(r'[a-zA-Z0-9_-]{1,128}', value):
        raise ConfigurationError('invalid_configuration_identifier')
    return value


def digest(data):
    return hashlib.sha256(data).hexdigest() if data is not None else None


def qualified_bytes(configuration):
    if (not isinstance(configuration, dict) or set(configuration) != {'version', 'enabled', 'listen_port'}
            or type(configuration['version']) is not int or configuration['version'] != 1
            or type(configuration['enabled']) is not bool or type(configuration['listen_port']) is not int
            or not 1024 <= configuration['listen_port'] <= 65535):
        raise ConfigurationError('unqualified_configuration')
    return (json.dumps(configuration, sort_keys=True, separators=(',', ':')) + '\n').encode()


def qualified_existing(data):
    if data is None:
        return
    if len(data) > MAX_CONFIG:
        raise ConfigurationError('unqualified_configuration')
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ConfigurationError('unqualified_configuration')
            result[key] = value
        return result
    def reject(_):
        raise ConfigurationError('unqualified_configuration')
    try:
        configuration = json.loads(data.decode('utf-8', errors='strict'), object_pairs_hook=pairs,
                                   parse_float=reject, parse_constant=reject)
        qualified_bytes(configuration)
    except (ValueError, UnicodeError, RecursionError, OverflowError):
        raise ConfigurationError('unqualified_configuration') from None


class ConfigurationManager:
    """Private journal/backup custody; production service enforces root identity.

    Custom registries/checkpoints are trusted source injection for isolated tests,
    never an IPC option. Same-UID/root hostile code is outside this file boundary.
    """
    def __init__(self, directory=Path('/var/lib/toddy/executor/configuration'), *, registry=None,
                 clock=time.time, checkpoint=lambda _phase, _operation: None,
                 max_operations=64, byte_limit=1024 * 1024):
        self.directory = Path(directory)
        self.registry = dict(DEFAULT_REGISTRY if registry is None else registry)
        self.clock, self.checkpoint = clock, checkpoint
        self.max_operations, self.byte_limit = max_operations, byte_limit
        if (not self.directory.is_absolute() or self.directory.resolve() != self.directory
                or not 1 <= max_operations <= 1024 or byte_limit < 131072):
            raise ConfigurationError('unsafe_configuration_store')
        if len(set(self.registry.values())) != len(self.registry):
            raise ConfigurationError('unsafe_configuration_registry')
        for name, path in self.registry.items():
            identifier(name)
            if not isinstance(path, Path) or not path.is_absolute() or path.resolve() != path:
                raise ConfigurationError('unsafe_configuration_registry')
        self.directory.mkdir(mode=0o700, exist_ok=True)
        directory_info = self.directory.lstat()
        if (not stat.S_ISDIR(directory_info.st_mode) or directory_info.st_uid != os.geteuid()
                or stat.S_IMODE(directory_info.st_mode) != 0o700):
            raise ConfigurationError('unsafe_configuration_store')
        self.backups = self.directory / 'backups'
        self.backups.mkdir(mode=0o700, exist_ok=True)
        for path in (self.directory, self.backups):
            info = path.lstat()
            if (path.resolve() != path or not stat.S_ISDIR(info.st_mode) or info.st_uid != os.geteuid()
                    or stat.S_IMODE(info.st_mode) != 0o700):
                raise ConfigurationError('unsafe_configuration_store')
        for name in ('journal.sqlite', 'configuration.lock'):
            descriptor = os.open(self.directory / name, os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW | os.O_CLOEXEC, 0o600)
            try:
                self._private_file(os.fstat(descriptor))
            finally:
                os.close(descriptor)
        with self._db() as db:
            db.executescript('''
                CREATE TABLE IF NOT EXISTS configuration_operations(
                    id TEXT PRIMARY KEY,request_hash TEXT NOT NULL,kind TEXT NOT NULL,
                    config_id TEXT NOT NULL,state TEXT NOT NULL,before_hash TEXT,after_hash TEXT,
                    before_uid INTEGER,before_gid INTEGER,before_mode INTEGER,
                    after_uid INTEGER,after_gid INTEGER,after_mode INTEGER,
                    rollback_of TEXT,created REAL NOT NULL,updated REAL NOT NULL);
                CREATE TABLE IF NOT EXISTS desired_configurations(
                    config_id TEXT PRIMARY KEY,desired_hash TEXT,revision_id TEXT NOT NULL,
                    uid INTEGER,gid INTEGER,mode INTEGER,updated REAL NOT NULL);
            ''')

    @staticmethod
    def _private_file(info):
        if (not stat.S_ISREG(info.st_mode) or info.st_uid != os.geteuid() or info.st_nlink != 1
                or stat.S_IMODE(info.st_mode) != 0o600):
            raise ConfigurationError('unsafe_configuration_store_file')

    @contextmanager
    def _db(self):
        db = sqlite3.connect(self.directory / 'journal.sqlite', timeout=5, isolation_level=None)
        db.row_factory = sqlite3.Row
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

    @contextmanager
    def _lock(self):
        with open(self.directory / 'configuration.lock', 'r+b') as lock:
            try:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                raise ConfigurationError('configuration_busy') from None
            yield

    def _target(self, config_id):
        identifier(config_id)
        if config_id not in self.registry:
            raise ConfigurationError('configuration_not_registered')
        return self.registry[config_id]

    @staticmethod
    def _expected(value):
        if value is not None and (not isinstance(value, str) or not re.fullmatch(r'[a-f0-9]{64}', value)):
            raise ConfigurationError('invalid_configuration_hash')

    @staticmethod
    def _parent(path):
        descriptor = os.open('/', os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC)
        try:
            for name in path.parts[1:-1]:
                child = os.open(name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC, dir_fd=descriptor)
                os.close(descriptor); descriptor = child
            info = os.fstat(descriptor)
            if info.st_uid != os.geteuid() or info.st_mode & 0o022:
                raise ConfigurationError('unsafe_configuration_parent')
            return descriptor
        except BaseException:
            os.close(descriptor)
            raise

    @staticmethod
    def _read(parent, name):
        try:
            descriptor = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_NOCTTY | os.O_CLOEXEC, dir_fd=parent)
        except FileNotFoundError:
            return None, None
        with os.fdopen(descriptor, 'rb') as incoming:
            info = os.fstat(incoming.fileno())
            if (not stat.S_ISREG(info.st_mode) or info.st_nlink != 1 or info.st_uid != os.geteuid()
                    or info.st_size > MAX_CONFIG or info.st_mode & 0o7133 or os.listxattr(incoming.fileno())):
                raise ConfigurationError('unsafe_configuration_target')
            data = incoming.read(MAX_CONFIG + 1)
            qualified_existing(data)
            return data, info

    @staticmethod
    def _metadata(info):
        return (info.st_uid, info.st_gid, stat.S_IMODE(info.st_mode)) if info else (None, None, None)

    @staticmethod
    def _same(before, current):
        if before is None or current is None:
            return before is current
        return (before.st_dev, before.st_ino, before.st_uid, before.st_gid, stat.S_IMODE(before.st_mode)) == (
            current.st_dev, current.st_ino, current.st_uid, current.st_gid, stat.S_IMODE(current.st_mode))

    def _capacity(self, db, *, restoring):
        count = db.execute('SELECT count(*) FROM configuration_operations').fetchone()[0]
        if count >= self.max_operations + (4 if restoring else 0):
            raise ConfigurationError('configuration_store_full')
        used = sum(path.stat().st_size for path in self.directory.rglob('*') if path.is_file())
        limit = self.byte_limit if restoring else self.byte_limit - 65536
        if used + 32768 > limit or shutil.disk_usage(self.directory).free < 65536:
            raise ConfigurationError('configuration_store_full')

    def _backup(self, operation_id, before):
        if before is None:
            return
        descriptor = os.open(self.backups / (operation_id + '.json'),
                             os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_CLOEXEC, 0o600)
        with os.fdopen(descriptor, 'wb') as output:
            output.write(before); output.flush(); os.fsync(output.fileno())
        folder = os.open(self.backups, os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC)
        try:
            os.fsync(folder)
        finally:
            os.close(folder)

    def _backup_bytes(self, row):
        if row['before_hash'] is None:
            return None
        descriptor = os.open(self.backups / (row['id'] + '.json'), os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_NOCTTY | os.O_CLOEXEC)
        with os.fdopen(descriptor, 'rb') as incoming:
            self._private_file(os.fstat(incoming.fileno()))
            data = incoming.read(MAX_CONFIG + 1)
        qualified_existing(data)
        if digest(data) != row['before_hash']:
            raise ConfigurationError('configuration_backup_corrupt')
        return data

    @staticmethod
    def _receipt(row):
        return {'version': 1, 'config_id': row['config_id'], 'revision_id': row['id'],
                'kind': row['kind'], 'state': row['state'],
                'verified': row['state'] in {'completed', 'canceled', 'not_applied'},
                'changed': row['state'] == 'completed', 'before_sha256': row['before_hash'],
                'after_sha256': row['after_hash'] if row['state'] == 'completed' else row['before_hash']}

    def operation(self, operation_id):
        identifier(operation_id)
        with self._db() as db:
            row = db.execute('SELECT * FROM configuration_operations WHERE id=?', (operation_id,)).fetchone()
            if row is None:
                raise ConfigurationError('configuration_revision_unknown')
            return self._receipt(row)

    def _record_complete(self, operation_id):
        with self._transaction() as db:
            row = db.execute('SELECT * FROM configuration_operations WHERE id=?', (operation_id,)).fetchone()
            db.execute("UPDATE configuration_operations SET state='completed',updated=? WHERE id=?", (self.clock(), operation_id))
            db.execute('INSERT OR REPLACE INTO desired_configurations VALUES(?,?,?,?,?,?,?)',
                       (row['config_id'], row['after_hash'], operation_id, row['after_uid'], row['after_gid'], row['after_mode'], self.clock()))

    def _replace(self, parent, name, before, before_info, after, after_metadata, canceled):
        temporary = None
        try:
            if after is not None:
                temporary = '.toddy-managed-' + secrets.token_hex(16)
                descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_CLOEXEC, 0o600, dir_fd=parent)
                with os.fdopen(descriptor, 'wb') as output:
                    os.fchown(output.fileno(), after_metadata[0], after_metadata[1])
                    os.fchmod(output.fileno(), after_metadata[2])
                    output.write(after); output.flush(); os.fsync(output.fileno())
            current, info = self._read(parent, name)
            if digest(current) != digest(before) or not self._same(before_info, info):
                raise ConfigurationError('configuration_owner_drift')
            if canceled():
                return False
            if after is None:
                os.unlink(name, dir_fd=parent)
            else:
                os.replace(temporary, name, src_dir_fd=parent, dst_dir_fd=parent); temporary = None
            os.fsync(parent)
            verified, info = self._read(parent, name)
            if digest(verified) != digest(after) or self._metadata(info) != after_metadata:
                raise ConfigurationError('configuration_postcondition_failed')
            return True
        finally:
            if temporary:
                try:
                    os.unlink(temporary, dir_fd=parent)
                except FileNotFoundError:
                    pass

    def _change(self, operation_id, config_id, after, expected_sha256, *, kind, rollback_of=None,
                restored_metadata=None, canceled=lambda: False):
        identifier(operation_id); self._expected(expected_sha256)
        path = self._target(config_id)
        request = digest(json.dumps({'kind': kind, 'config_id': config_id, 'after': digest(after),
            'expected': expected_sha256, 'rollback_of': rollback_of}, sort_keys=True, separators=(',', ':')).encode())
        with self._lock():
            with self._db() as db:
                old = db.execute('SELECT * FROM configuration_operations WHERE id=?', (operation_id,)).fetchone()
                if old:
                    if old['request_hash'] != request:
                        raise ConfigurationError('configuration_operation_conflict')
                    if old['state'] not in {'completed', 'canceled', 'not_applied'}:
                        raise ConfigurationError('configuration_reconciliation_required')
                    return self._receipt(old)
                if db.execute("SELECT 1 FROM configuration_operations WHERE config_id=? AND state IN ('preparing','prepared','uncertain')", (config_id,)).fetchone():
                    raise ConfigurationError('configuration_reconciliation_required')
            if canceled():
                raise ConfigurationError('configuration_canceled_before_preparation')
            parent = self._parent(path)
            try:
                before, info = self._read(parent, path.name)
                if digest(before) != expected_sha256:
                    raise ConfigurationError('configuration_owner_drift')
                if kind == 'restore':
                    with self._db() as db:
                        active = db.execute('SELECT * FROM desired_configurations WHERE config_id=?', (config_id,)).fetchone()
                    if active is None or active['revision_id'] != rollback_of:
                        raise ConfigurationError('configuration_revision_changed')
                    if self._metadata(info) != (active['uid'], active['gid'], active['mode']):
                        raise ConfigurationError('configuration_owner_drift')
                before_metadata = self._metadata(info)
                after_metadata = (restored_metadata if after is not None else (None, None, None)) if kind == 'restore' else (
                    before_metadata if info else (os.geteuid(), os.getegid(), 0o644))
                if shutil.disk_usage(path.parent).free < 8192:
                    raise ConfigurationError('configuration_target_full')
                with self._transaction() as db:
                    self._capacity(db, restoring=kind == 'restore')
                    now = self.clock()
                    db.execute('INSERT INTO configuration_operations VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)',
                        (operation_id, request, kind, config_id, 'preparing', digest(before), digest(after),
                         *before_metadata, *after_metadata, rollback_of, now, now))
                self._backup(operation_id, before)
                with self._transaction() as db:
                    db.execute("UPDATE configuration_operations SET state='prepared',updated=? WHERE id=?", (self.clock(), operation_id))
                self.checkpoint('prepared', operation_id)
                if not self._replace(parent, path.name, before, info, after, after_metadata, canceled):
                    with self._transaction() as db:
                        db.execute("UPDATE configuration_operations SET state='canceled',updated=? WHERE id=?", (self.clock(), operation_id))
                    return self.operation(operation_id)
                self.checkpoint('after_effect', operation_id)
                self._record_complete(operation_id)
                return self.operation(operation_id)
            finally:
                os.close(parent)

    def apply(self, operation_id, config_id, configuration, expected_sha256, *, canceled=lambda: False):
        return self._change(operation_id, config_id, qualified_bytes(configuration), expected_sha256,
                            kind='apply', canceled=canceled)

    def restore(self, operation_id, config_id, revision_id, expected_sha256, *, canceled=lambda: False):
        identifier(revision_id); self._expected(expected_sha256)
        with self._db() as db:
            row = db.execute('SELECT * FROM configuration_operations WHERE id=? AND config_id=?', (revision_id, config_id)).fetchone()
            if row is None or row['state'] != 'completed':
                raise ConfigurationError('configuration_revision_unknown')
            if row['after_hash'] != expected_sha256:
                raise ConfigurationError('configuration_revision_changed')
            before = self._backup_bytes(row)
            metadata = (row['before_uid'], row['before_gid'], row['before_mode'])
        return self._change(operation_id, config_id, before, expected_sha256, kind='restore', rollback_of=revision_id,
                            restored_metadata=metadata, canceled=canceled)

    def inspect(self, config_id):
        path = self._target(config_id)
        with self._db() as db:
            desired = db.execute('SELECT * FROM desired_configurations WHERE config_id=?', (config_id,)).fetchone()
        try:
            parent = self._parent(path)
            try:
                data, info = self._read(parent, path.name)
            finally:
                os.close(parent)
            actual_hash, metadata, qualified = digest(data), self._metadata(info), True
        except (ConfigurationError, OSError):
            actual_hash, metadata, qualified = None, (None, None, None), False
        expected = (desired['uid'], desired['gid'], desired['mode']) if desired else metadata
        return {'version': 1, 'config_id': config_id, 'managed': desired is not None,
                'qualification_only': True, 'qualified': qualified, 'actual_sha256': actual_hash,
                'desired_sha256': desired['desired_hash'] if desired else None,
                'revision_id': desired['revision_id'] if desired else None,
                'drift': not qualified or bool(desired and (actual_hash != desired['desired_hash'] or metadata != expected))}

    def reconcile(self, operation_id):
        """Read/verify existing state only. Never dispatch or repeat a replacement."""
        identifier(operation_id)
        with self._lock():
            with self._db() as db:
                row = db.execute('SELECT * FROM configuration_operations WHERE id=?', (operation_id,)).fetchone()
                if row is None:
                    raise ConfigurationError('configuration_revision_unknown')
                if row['state'] in {'completed', 'canceled', 'not_applied'}:
                    return self._receipt(row)
            path = self._target(row['config_id'])
            parent = self._parent(path)
            try:
                current, info = self._read(parent, path.name)
            finally:
                os.close(parent)
            metadata = self._metadata(info)
            if row['state'] in {'prepared', 'uncertain'} and digest(current) == row['after_hash'] and metadata == (row['after_uid'], row['after_gid'], row['after_mode']):
                self._backup_bytes(row)
                self._record_complete(operation_id)
                return self.operation(operation_id)
            if digest(current) == row['before_hash'] and metadata == (row['before_uid'], row['before_gid'], row['before_mode']):
                with self._transaction() as db:
                    db.execute("UPDATE configuration_operations SET state='not_applied',updated=? WHERE id=?", (self.clock(), operation_id))
                return self.operation(operation_id)
            return {**self._receipt(row), 'state': 'review_required', 'verified': False, 'changed': False}

    def rescue_manifest(self, revision_id):
        """Trusted owner/manual rescue metadata only; no root IPC arbitrary path API."""
        identifier(revision_id)
        with self._db() as db:
            row = db.execute('SELECT * FROM configuration_operations WHERE id=?', (revision_id,)).fetchone()
            if row is None or row['state'] != 'completed':
                raise ConfigurationError('configuration_revision_unknown')
            self._backup_bytes(row)
            return {'version': 1, 'config_id': row['config_id'], 'target': str(self._target(row['config_id'])),
                    'backup_file': str(self.backups / (revision_id + '.json')) if row['before_hash'] else None,
                    'backup_sha256': row['before_hash'], 'was_absent': row['before_hash'] is None,
                    'uid': row['before_uid'], 'gid': row['before_gid'], 'mode': row['before_mode']}


def validate_request(kind, arguments):
    """Pure public schema; source registry/operation identity stay out of JSON."""
    fields = {'managed_config_apply': {'config_id', 'configuration', 'expected_sha256'},
              'managed_config_restore': {'config_id', 'revision_id', 'expected_sha256'}}.get(kind)
    if fields is None or not isinstance(arguments, dict) or set(arguments) != fields:
        raise ConfigurationError('invalid_managed_configuration_operation')
    identifier(arguments['config_id'])
    if arguments['config_id'] not in DEFAULT_REGISTRY:
        raise ConfigurationError('configuration_not_registered')
    ConfigurationManager._expected(arguments['expected_sha256'])
    if kind == 'managed_config_apply':
        qualified_bytes(arguments['configuration'])
    else:
        identifier(arguments['revision_id'])
    return arguments


def dispatch(operation_id, kind, arguments, canceled=lambda: False):
    """Root service entry; operation_id must be its authenticated durable ID."""
    if os.geteuid() != 0 or os.getuid() != 0:
        raise ConfigurationError('root_executor_required')
    identifier(operation_id)
    validate_request(kind, arguments)
    manager = ConfigurationManager()
    if kind == 'managed_config_apply':
        return manager.apply(operation_id, arguments['config_id'], arguments['configuration'],
                             arguments['expected_sha256'], canceled=canceled)
    return manager.restore(operation_id, arguments['config_id'], arguments['revision_id'],
                           arguments['expected_sha256'], canceled=canceled)
