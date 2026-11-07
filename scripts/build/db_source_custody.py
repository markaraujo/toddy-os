"""Protect completed database diagnostic inputs without changing raw results."""
from collections import Counter
import fcntl
import json
import os
from pathlib import Path
import stat
import tempfile

import db_coverage_result
from db_standard_result import digest, protected

BUILD = Path('/var/log/toddy/build')


def snapshot(source):
    paths = [source]
    for directory, directories, files in os.walk(source, followlinks=False):
        paths.extend(Path(directory) / name for name in directories + files)
    result = {}
    links = Counter()
    for path in paths:
        info = path.lstat()
        kind = stat.S_IFMT(info.st_mode)
        if kind not in (stat.S_IFDIR, stat.S_IFREG, stat.S_IFLNK):
            raise ValueError('Special entry in completed source: ' + str(path))
        if not path.resolve().is_relative_to(source):
            raise ValueError('Source alias escapes the completed fixture: ' + str(path))
        row = {'device': info.st_dev, 'inode': info.st_ino, 'kind': kind,
               'mode': stat.S_IMODE(info.st_mode), 'uid': info.st_uid,
               'gid': info.st_gid, 'links': info.st_nlink}
        result[str(path.relative_to(source))] = row
        if kind == stat.S_IFREG:
            links[(info.st_dev, info.st_ino)] += 1
    for row in result.values():
        if row['kind'] == stat.S_IFREG and row['links'] != links[(row['device'], row['inode'])]:
            raise ValueError('Source inode has a hardlink outside the protected tree')
    return result


def refuse_open_references(tree):
    identities = {(row['device'], row['inode']) for row in tree.values()}
    for proc in Path('/proc').iterdir():
        if not proc.name.isdigit() or int(proc.name) == os.getpid():
            continue
        try:
            for path in [proc / 'cwd', proc / 'root', *list((proc / 'fd').iterdir())]:
                try:
                    info = path.stat()
                except (FileNotFoundError, ProcessLookupError):
                    continue
                if (info.st_dev, info.st_ino) in identities:
                    raise ValueError('Completed source still referenced by process ' + proc.name)
            for line in (proc / 'maps').read_text().splitlines():
                fields = line.split(maxsplit=5)
                major, minor = (int(part, 16) for part in fields[3].split(':'))
                if (os.makedev(major, minor), int(fields[4])) in identities:
                    raise ValueError('Completed source still mapped by process ' + proc.name)
        except (FileNotFoundError, ProcessLookupError):
            continue


def save(path, value):
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode='w', prefix='.' + path.name + '.pending-',
                                         dir=path.parent, delete=False) as stream:
            temporary = Path(stream.name)
            os.fchmod(stream.fileno(), 0o600)
            json.dump(value, stream, indent=2)
            stream.write('\n')
            stream.flush()
            os.fsync(stream.fileno())
        # Same-filesystem exclusive publication: never replace an older record,
        # and never expose a partially written JSON file under its final name.
        os.link(temporary, path)
        descriptor = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
    finally:
        if temporary is not None:
            temporary.unlink()


def require_protected_tree(tree):
    if any(row['uid'] or row['gid'] or (row['kind'] != stat.S_IFLNK and row['mode'] & 0o022)
           for row in tree.values()):
        raise ValueError('Unprotected source metadata remains')


def verify_receipt(base, verified, current):
    source = base / 'source'
    intent = base / 'source-custody.intent.json'
    receipt = base / 'source-custody.json'
    protected(receipt, private=True)
    protected(intent, private=True)
    protected(base, private=True, directory=True)
    protected(source, private=True, directory=True)
    require_protected_tree(current)
    result = json.loads(receipt.read_text())
    if (result.get('custody_sealed') is not True
            or result.get('suite_accepted') is not False or result.get('package_accepted') is not False
            or result['witness'] != verified or result['tree'] != current
            or result['intent_sha256'] != digest(intent)):
        raise ValueError('Protected custody evidence changed')
    return result


def verify_coverage_custody(base, standard):
    """Read-only evidence gate; a missing seal is an error, never a mutation."""
    base = Path(base)
    verified = db_coverage_result.verify(base, standard)
    current = snapshot(base / 'source')
    verify_receipt(base, verified, current)
    return dict(verified, custody_sealed=True, source_entries=len(current),
                custody_receipt_sha256=digest(base / 'source-custody.json'))


def seal_coverage(base, standard):
    """Only ADR-0083's actual terminal witness is eligible; no full-suite gate."""
    if os.geteuid() != 0:
        raise ValueError('Disposable guest root required')
    base, standard = Path(base), Path(standard)
    with (BUILD / 'build.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        if list(BUILD.glob('*.running.json')) or (BUILD / 'input-sync.running').exists():
            raise ValueError('Preserve active dispatcher or input synchronization')
        # Verify actual exits, dead producer, all 10,208 native inputs/reports
        # and the exact standard pairing before changing any fixture metadata.
        verified = db_coverage_result.verify(base, standard)
        return seal_verified_source(base, verified, lambda: db_coverage_result.verify(base, standard))


def seal_verified_source(base, verified, reverify):
    """Internal custody operation after terminal review under the dispatcher lock."""
    source = base / 'source'
    intent = base / 'source-custody.intent.json'
    receipt = base / 'source-custody.json'
    current = snapshot(source)
    if receipt.exists():
        return verify_receipt(base, verified, current)
    if intent.exists():
        protected(intent, private=True)
        original = json.loads(intent.read_text())
        if original['witness'] != verified or set(original['tree']) != set(current):
            raise ValueError('Interrupted custody belongs to different evidence')
        for name, row in current.items():
            if any(row[key] != original['tree'][name][key]
                   for key in ('device', 'inode', 'kind', 'links')):
                raise ValueError('Interrupted source inode changed: ' + name)
    else:
        save(intent, {'witness': verified, 'tree': current})
    # Close pathname access before checking held descriptors/mappings.
    # A refusal leaves the access gate closed and the intent for recovery.
    base.chmod(0o700)
    os.chown(source, 0, 0, follow_symlinks=False)
    source.chmod(0o700)
    refuse_open_references(current)
    for name, row in current.items():
        path = source / name
        info = path.lstat()
        if (info.st_dev, info.st_ino, stat.S_IFMT(info.st_mode)) != (row['device'], row['inode'], row['kind']):
            raise ValueError('Source inode changed while sealing: ' + name)
        os.chown(path, 0, 0, follow_symlinks=False)
        if row['kind'] != stat.S_IFLNK:
            path.chmod(0o700 if name == '.' else row['mode'] & ~0o022)
    final = snapshot(source)
    require_protected_tree(final)
    refuse_open_references(final)
    if reverify() != verified:
        raise ValueError('Native input/report bytes changed during custody transfer')
    result = {'custody_sealed': True, 'suite_accepted': False, 'package_accepted': False,
              'witness': verified, 'intent_sha256': digest(intent), 'tree': final}
    save(receipt, result)
    return result
