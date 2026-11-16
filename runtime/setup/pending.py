"""Private non-secret setup intent, independent of the optional agent backend.

This module never authorizes or executes acquisition. The current curated catalog
has no qualified releases: its candidates are unavailable, even when a deferred
wish is retained in an older installer handoff. Dispatch requires a later verified
release catalog, installed-user review and the native backend authorization path.
"""
from contextlib import contextmanager
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import stat

MAX_BYTES = 65536
ID = re.compile(r'[a-z][a-z0-9-]{0,63}\Z')
HASH = re.compile(r'[a-f0-9]{64}\Z')
ERRORS = {None, 'offline', 'unavailable', 'catalog_changed', 'review_required'}


class SetupError(ValueError):
    """A bounded code safe for a native setup view; no private path/data detail."""


def _strict(data):
    if not isinstance(data, bytes) or len(data) > MAX_BYTES:
        raise SetupError('manifest_size')

    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise SetupError('duplicate_field')
            result[key] = value
        return result

    def constant(_):
        raise SetupError('invalid_json')

    try:
        return json.loads(data.decode('utf-8'), object_pairs_hook=pairs,
                          parse_constant=constant)
    except (UnicodeError, json.JSONDecodeError, RecursionError) as exc:
        raise SetupError('invalid_json') from exc


def _identifier(value):
    return isinstance(value, str) and ID.fullmatch(value) is not None


def _digest(data):
    return hashlib.sha256(data).hexdigest()


def _encode(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode('utf-8')


class Catalog:
    """Read the bundled candidate catalog without treating it as trusted releases.

    Qualified release metadata verification/acquisition is deliberately outside
    this intent-only slice. Nonempty release records fail closed for now.
    """
    def __init__(self, data):
        self.revision = _digest(data)
        value = _strict(data)
        if not isinstance(value, dict) or value.get('schema_version') != 1 or \
                type(value.get('schema_version')) is not int or \
                not isinstance(value.get('candidates'), list):
            raise SetupError('invalid_catalog')
        if value.get('qualified_releases') != []:
            raise SetupError('release_verification_required')
        self.candidates = {}
        for row in value['candidates']:
            if not isinstance(row, dict) or not _identifier(row.get('id')) or \
                    row['id'] in self.candidates or row.get('default') not in {'off', 'required'}:
                raise SetupError('invalid_catalog')
            self.candidates[row['id']] = row

    def optional(self, choice_id):
        if not _identifier(choice_id) or choice_id not in self.candidates or \
                self.candidates[choice_id]['default'] != 'off':
            raise SetupError('invalid_choice')
        return self.candidates[choice_id]

    def review(self, manifest):
        """Return advisory status only, never an install plan/command or consent."""
        result = []
        for choice in manifest['choices']:
            self.optional(choice['id'])
            result.append({'id': choice['id'], 'availability': 'unavailable',
                           'reason': 'no_verified_release', 'can_install': False,
                           'catalog_changed': manifest['catalog_revision'] != self.revision})
        return result


def validate(value, catalog):
    if not isinstance(value, dict) or set(value) != {
            'schema_version', 'installation_id', 'catalog_revision', 'ai_choice',
            'choices', 'consent_receipts', 'invitation_dismissed'}:
        raise SetupError('invalid_manifest')
    if type(value['schema_version']) is not int or value['schema_version'] != 1 or \
            not _identifier(value['installation_id']) or \
            not isinstance(value['catalog_revision'], str) or not HASH.fullmatch(value['catalog_revision']) or \
            value['ai_choice'] not in ('later', 'api', 'local') or \
            type(value['invitation_dismissed']) is not bool:
        raise SetupError('invalid_manifest')
    # This slice supports intent only. Neither keys nor reusable authorization
    # receipts are accepted. Future acquisition must introduce a reviewed schema.
    if value['consent_receipts'] != [] or not isinstance(value['choices'], list) or \
            len(value['choices']) > len(catalog.candidates):
        raise SetupError('invalid_manifest')
    seen = set()
    for choice in value['choices']:
        if not isinstance(choice, dict) or set(choice) != {'id', 'artifact_id', 'state', 'error_code'}:
            raise SetupError('invalid_choice')
        catalog.optional(choice['id'])
        if choice['id'] in seen or choice['state'] != 'deferred' or \
                choice['artifact_id'] is not None or \
                (choice['error_code'] is not None and not isinstance(choice['error_code'], str)) or \
                choice['error_code'] not in ERRORS:
            raise SetupError('invalid_choice')
        seen.add(choice['id'])
    if len(_encode(value)) > MAX_BYTES:
        raise SetupError('manifest_size')
    return value


class PendingStore:
    """Owned 0700 setup directory and atomic 0600 pending.json with CAS.

    Pass the installed user's actual $XDG_STATE_HOME/toddy/setup directory.
    The installer must transfer ownership before invoking this user-side API.
    Parent directories belong to that platform handoff; this class refuses any
    symlink component. It does not claim isolation from other code of the same UID.
    """
    def __init__(self, directory, catalog):
        self.directory = Path(directory)
        self.catalog = catalog
        if not self.directory.is_absolute():
            raise SetupError('state_directory')
        for component in reversed((self.directory, *self.directory.parents)):
            if component.is_symlink():
                raise SetupError('state_directory')
        try:
            self.directory.mkdir(mode=0o700)
        except FileExistsError:
            pass
        info = self.directory.lstat()
        if not stat.S_ISDIR(info.st_mode) or info.st_uid != os.getuid() or \
                stat.S_IMODE(info.st_mode) != 0o700:
            raise SetupError('state_directory')
        self.dirfd = os.open(self.directory, os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC)

    def close(self):
        if self.dirfd is not None:
            os.close(self.dirfd)
            self.dirfd = None

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()

    @contextmanager
    def _locked(self):
        fd = os.open('.pending.lock', os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW | os.O_CLOEXEC,
                     0o600, dir_fd=self.dirfd)
        try:
            self._private_regular(fd)
            try:
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError as exc:
                raise SetupError('setup_busy') from exc
            yield
        finally:
            os.close(fd)

    @staticmethod
    def _private_regular(fd):
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid() or \
                stat.S_IMODE(info.st_mode) != 0o600 or info.st_nlink != 1:
            raise SetupError('state_file')

    def _read(self):
        try:
            fd = os.open('pending.json', os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC | os.O_NONBLOCK,
                         dir_fd=self.dirfd)
        except FileNotFoundError:
            return None, None
        try:
            self._private_regular(fd)
            with os.fdopen(fd, 'rb', closefd=False) as source:
                data = source.read(MAX_BYTES + 1)
            return validate(_strict(data), self.catalog), _digest(data)
        finally:
            os.close(fd)

    def load(self):
        with self._locked():
            return self._read()

    def create(self, installation_id):
        """Create empty deferred setup after verified base installation only."""
        value = {'schema_version': 1, 'installation_id': installation_id,
                 'catalog_revision': self.catalog.revision, 'ai_choice': 'later',
                 'choices': [], 'consent_receipts': [], 'invitation_dismissed': False}
        return self.save(value, expected_revision=None)

    def save(self, value, *, expected_revision):
        """Persist validated intent only; None means create-if-absent.

        Choice rows from a prior installer may be retained as deferred wishes;
        unavailable candidates remain unavailable and cannot authorize acquisition.
        """
        data = _encode(validate(value, self.catalog))
        with self._locked():
            current, revision = self._read()
            if revision != expected_revision:
                raise SetupError('stale_revision')
            if current is not None and current['installation_id'] != value['installation_id']:
                raise SetupError('installation_changed')
            name = '.pending-' + os.urandom(16).hex()
            fd = os.open(name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_CLOEXEC,
                         0o600, dir_fd=self.dirfd)
            try:
                with os.fdopen(fd, 'wb', closefd=False) as target:
                    target.write(data)
                    target.flush()
                    os.fsync(fd)
                os.replace(name, 'pending.json', src_dir_fd=self.dirfd, dst_dir_fd=self.dirfd)
                os.fsync(self.dirfd)
            finally:
                os.close(fd)
                try:
                    os.unlink(name, dir_fd=self.dirfd)
                except FileNotFoundError:
                    pass
            return _digest(data)

    def dismiss(self, *, expected_revision):
        value, revision = self.load()
        if value is None or revision != expected_revision:
            raise SetupError('stale_revision')
        value['invitation_dismissed'] = True
        return self.save(value, expected_revision=revision)
