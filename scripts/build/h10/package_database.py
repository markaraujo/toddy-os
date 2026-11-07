"""Copy a quiescent native Dpkg database into fresh image staging.

This component verifies database structure/own-record agreement, not installed
payload or final dependency closure. The image assembler must also require those
independent acceptance checks. No installed-target mutation entry point exists.
"""
from contextlib import contextmanager
import errno
import fcntl
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import stat
import threading

LOCKS = ('lock-frontend', 'lock')
DIRECTORIES = {'info', 'updates', 'parts', 'alternatives', 'triggers', 'methods',
               'methods/file', 'methods/ftp', 'methods/mnt', 'methods/media'}
EMPTY_STATE = {*LOCKS, 'triggers/Lock', 'triggers/Unincorp'}
QUERY = '${Package}\t${Version}\t${Architecture}\t${Status}\n'
_ACTIVE_LOCKS = {}
_LOCK_REGISTRY = threading.RLock()


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


@contextmanager
def database_lock(database):
    """Share descriptor lifetime across nested native Dpkg read transactions.

    Closing any descriptor for a POSIX-locked inode releases this process's
    locks, even if another descriptor/context still needs them. Reuse the same
    descriptors and close only after the last context exits. Registry changes
    are serialized; the actual image work does not hold the registry mutex.
    """
    database = Path(database)
    if database.resolve() != database or not database.is_dir():
        raise ValueError('Native database must be a physical canonical directory')
    info = database.stat()
    key = (os.getpid(), info.st_dev, info.st_ino)
    with _LOCK_REGISTRY:
        held = _ACTIVE_LOCKS.get(key)
        if held is not None:
            # lstat/fstat do not reopen and close the locked inodes. Refuse
            # replaced paths rather than accidentally acquiring another file.
            for name, fd in zip(LOCKS, held['descriptors']):
                actual, original = (database / name).lstat(), os.fstat(fd)
                if (actual.st_dev, actual.st_ino) != (original.st_dev, original.st_ino):
                    raise ValueError('Native lock inode changed during an active read transaction')
            held['references'] += 1
        else:
            descriptors = []
            try:
                for name in LOCKS:
                    path = database / name
                    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
                    descriptors.append(fd)
                    info = os.fstat(fd)
                    if (not stat.S_ISREG(info.st_mode) or info.st_uid != 0 or info.st_gid != 0
                            or info.st_nlink != 1 or info.st_size != 0):
                        raise ValueError('Unexpected native package lock metadata')
                    try:
                        fcntl.lockf(fd, fcntl.LOCK_SH | fcntl.LOCK_NB)
                    except OSError as error:
                        if error.errno not in (errno.EACCES, errno.EAGAIN):
                            raise
                        raise ValueError('A package writer is active; preserve state and retry after completion') from error
            except BaseException:
                for fd in reversed(descriptors):
                    os.close(fd)
                raise
            held = {'descriptors': descriptors, 'references': 1}
            _ACTIVE_LOCKS[key] = held
    try:
        yield
    finally:
        with _LOCK_REGISTRY:
            held['references'] -= 1
            if held['references'] == 0:
                del _ACTIVE_LOCKS[key]
                for fd in reversed(held['descriptors']):
                    os.close(fd)


def snapshot(database):
    if database.resolve() != database or not database.is_dir():
        raise ValueError('Database directory redirects or is missing')
    entries = {}
    device = database.stat().st_dev
    for parent, directories, files in os.walk(database, followlinks=False):
        for name in directories + files:
            path = Path(parent) / name
            relative = path.relative_to(database).as_posix()
            info = path.lstat()
            if (info.st_dev != device or path.parent.resolve() != path.parent
                    or info.st_uid != 0 or info.st_gid != 0 or os.listxattr(path, follow_symlinks=False)):
                raise ValueError('Unexpected database location, ownership or extended metadata: ' + relative)
            row = {'mode': info.st_mode, 'uid': info.st_uid, 'gid': info.st_gid,
                   'mtime_ns': info.st_mtime_ns, 'size': info.st_size}
            if stat.S_ISDIR(info.st_mode):
                if relative not in DIRECTORIES or stat.S_IMODE(info.st_mode) != 0o755:
                    raise ValueError('Unreviewed package database directory: ' + relative)
            elif stat.S_ISREG(info.st_mode) and info.st_nlink == 1:
                if relative in EMPTY_STATE:
                    if info.st_size:
                        raise ValueError('Pending package transaction/trigger state: ' + relative)
                    # Closing *any* descriptor for a POSIX-locked inode would
                    # release this process's locks. Never reopen/hash lock files.
                    row['sha256'] = hashlib.sha256(b'').hexdigest()
                    if relative in LOCKS:
                        # Dpkg opens both lock files with O_TRUNC before it
                        # attempts F_SETLK. A correctly rejected writer can
                        # therefore update empty lock-file mtimes, not DB data.
                        row.pop('mtime_ns')
                elif relative in {'status', 'status-old'} or relative.startswith('info/'):
                    if stat.S_IMODE(info.st_mode) != 0o644:
                        raise ValueError('Unexpected package database file mode: ' + relative)
                    row['sha256'] = digest(path)
                else:
                    raise ValueError('Unreviewed or interrupted package state: ' + relative)
            else:
                raise ValueError('Redirected, shared or special package database file: ' + relative)
            entries[relative] = row
    if 'status' not in entries or 'info' not in entries:
        raise ValueError('Missing native package database state')
    return entries


def canonical_path(value, relative=False):
    path = PurePosixPath(value)
    if (not value or '\0' in value or '\n' in value or '..' in path.parts
            or path.as_posix() != value or value.startswith('//')
            or path.is_absolute() == relative):
        raise ValueError('Noncanonical package database payload path')
    return '/' + value if relative else value


def validate_info(database, records, entries):
    """Require native file lists/checksum namespaces to match own package records.

    Stored MD5 values remain native Dpkg metadata, not independent authenticity
    evidence. SHA-256 payload/archive verification is a separate image preflight.
    """
    expected_files = {'info/format'} if 'info/format' in entries else set()
    if 'info/format' in entries and (database / 'info/format').read_text() != '1\n':
        raise ValueError('Unsupported native database info format')
    counts = {'packages': len(records), 'file_list_entries': 0, 'md5_entries': 0, 'conffiles': 0}
    if not records:
        raise ValueError('Empty own-package record set')
    for name, record in records.items():
        if (not re.fullmatch(r'[a-z0-9][a-z0-9+.-]+', name) or record['name'] != name
                or record.get('installed') is not True
                or not re.fullmatch(r'[0-9a-f]{64}', record['archive_sha256'])):
            raise ValueError('Unexpected installed own-package record')
        payload = record['payload']
        listing = database / ('info/' + name + '.list')
        lines = listing.read_text().splitlines()
        paths = [canonical_path(path) for path in lines if path != '/.']
        if lines.count('/.') != 1 or len(paths) != len(set(paths)) or set(paths) != set(payload):
            raise ValueError('Native file list differs from own record: ' + name)
        expected_files.update(('info/' + name + '.list', 'info/' + name + '.md5sums'))
        sums = {}
        for line in (database / ('info/' + name + '.md5sums')).read_text().splitlines():
            match = re.fullmatch(r'([0-9a-f]{32})  (.+)', line)
            if not match:
                raise ValueError('Malformed native checksum entry: ' + name)
            path = canonical_path(match[2], relative=True)
            if path in sums:
                raise ValueError('Duplicate native checksum entry: ' + name)
            sums[path] = match[1]
        if set(sums) != {path for path, row in payload.items() if 'sha256' in row}:
            raise ValueError('Native checksum namespace differs from own payload: ' + name)
        conffile_path = 'info/' + name + '.conffiles'
        if conffile_path in entries:
            conf = (database / conffile_path).read_text().splitlines()
            if (not conf or len(conf) != len(set(conf))
                    or any(canonical_path(path) not in sums or not path.startswith('/etc/') for path in conf)):
                raise ValueError('Unexpected native conffile namespace: ' + name)
            counts['conffiles'] += len(conf)
            expected_files.add(conffile_path)
        counts['file_list_entries'] += len(lines)
        counts['md5_entries'] += len(sums)
    if {name for name in entries if name.startswith('info/')} != expected_files:
        raise ValueError('Unknown package metadata or maintainer program in native database')
    return counts


def stage_database(backend, destination, records_directory):
    root, destination, records_directory = map(Path, (backend.target, destination, records_directory))
    if not backend.native or root.resolve() != root or os.geteuid() != 0:
        raise ValueError('Package database staging requires the accepted native disposable target')
    if (destination.is_symlink() or destination.parent.resolve() != destination.parent
            or not any(destination.is_relative_to(root / area) for area in ('tmp', 'sources/stage'))):
        raise ValueError('Preserve existing/outside/redirected database stage')
    retained_directories = []
    if destination.exists():
        # Native Dpkg owns these empty directories. Image payload copying may
        # already have created them; retain their exact safe metadata, but never
        # merge with any preexisting package state or unknown directory.
        paths = [destination]
        for parent, directories, files in os.walk(destination, followlinks=False):
            paths.extend(Path(parent) / name for name in directories + files)
        for path in paths:
            relative = path.relative_to(destination).as_posix()
            info = path.lstat()
            if (relative not in {'.', *DIRECTORIES} or info.st_mode != stat.S_IFDIR | 0o755
                    or info.st_uid != 0 or info.st_gid != 0 or info.st_dev != root.stat().st_dev
                    or path.resolve() != path or os.listxattr(path, follow_symlinks=False)):
                raise ValueError('Preserve populated or unreviewed database stage: ' + relative)
            retained_directories.append(relative)
    database = root / 'var/lib/dpkg'
    def query(path):
        return backend.run('dpkg-query', '--admindir=/' + str(path.relative_to(root)), '-W',
                           '-f=' + QUERY, capture_output=True, text=True).stdout
    def audit(path):
        result = backend.run('dpkg', '--admindir=/' + str(path.relative_to(root)), '--audit',
                             capture_output=True, text=True)
        if result.stdout or result.stderr:
            raise ValueError('Native database audit produced diagnostics: ' + result.stdout + result.stderr)
    with database_lock(database):
        before = snapshot(database)
        identities = query(database)
        records, record_hashes = {}, {}
        for line in identities.splitlines():
            name, version, architecture, status = line.split('\t')
            if (status != 'install ok installed' or name in records
                    or not re.fullmatch(r'[a-z0-9][a-z0-9+.-]+', name)
                    or not re.fullmatch(r'[0-9][0-9A-Za-z.+:~_-]*', version)
                    or architecture not in {'amd64', 'all'}):
                raise ValueError('Incomplete or unreviewed native package identity')
            path = records_directory / f'{name}_{version}_{architecture}.json'
            if path.resolve() != path:
                raise ValueError('Own-package provenance redirects')
            raw = path.read_bytes()
            record = json.loads(raw)
            if record['version'] != version:
                raise ValueError('Installed version differs from own record')
            records[name] = record
            record_hashes[str(path)] = hashlib.sha256(raw).hexdigest()
        counts = validate_info(database, records, before)
        audit(database)
        if snapshot(database) != before:
            raise ValueError('Database changed during source preflight')
        selected = sorted(name for name in before if name == 'status' or name.startswith('info/'))
        destination.mkdir(mode=0o755, exist_ok=True)
        destination.chmod(0o755)
        for directory in sorted(DIRECTORIES):
            (destination / directory).mkdir(mode=0o755, exist_ok=True)
            (destination / directory).chmod(0o755)
        for name in selected:
            shutil.copy2(database / name, destination / name)
        copied = snapshot(destination)
        for name in selected:
            if copied[name] != before[name]:
                raise ValueError('Copied package database bytes/metadata differ: ' + name)
        if sorted(name for name, row in copied.items() if stat.S_ISREG(row['mode'])) != selected:
            raise ValueError('Unexpected copied package database file')
        if query(destination) != identities:
            raise ValueError('Native package identities changed in staged database')
        audit(destination)
        validate_info(destination, records, copied)
        if snapshot(destination) != copied or snapshot(database) != before:
            raise ValueError('Source or staged database changed during native readback')
        if any(digest(Path(path)) != sha for path, sha in record_hashes.items()):
            raise ValueError('Own-package records changed during database staging')
    return {'counts': counts, 'copied_files': len(selected),
            'retained_empty_directories': sorted(retained_directories),
            'copied_bytes': sum(copied[name]['size'] for name in selected),
            'files': {name: copied[name]['sha256'] for name in selected},
            'omitted_source_files': sorted(name for name, row in before.items()
                                            if stat.S_ISREG(row['mode']) and name not in selected),
            'native_query_identical': True, 'native_audit_clean': True,
            'source_database_unchanged': True, 'record_sha256': record_hashes,
            'installed_payload_verified': False, 'full_image_or_dependency_closure_verified': False}
