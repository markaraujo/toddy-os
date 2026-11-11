"""Verify and extract the frozen browser source onto its dedicated build disk."""
from pathlib import Path, PurePosixPath
import fcntl
import hashlib
import json
import os
import subprocess
import tarfile

BASE = Path('/mnt/lfs/sources/phase2/work/firefox-1')
LOG = Path('/var/log/toddy/phase2')


def main():
    assert os.geteuid() == 0
    subprocess.run(['bash', '-c', 'source /opt/toddy-build/scripts/build/target.sh; guard_target'], check=True)
    lock = open('/var/log/toddy/build/build.lock', 'a')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    assert not list(Path('/var/log/toddy/build').glob('*.running.json'))
    receipt = LOG / 'firefox-source-1.json'
    assert not receipt.exists() and not receipt.with_suffix('.part').exists(), 'Inspect extraction; never replay'
    volume = json.loads((LOG / 'firefox-work-volume-1.json').read_text())
    assert volume['state'] == 'mounted'
    assert subprocess.check_output(['findmnt', '-n', '-o', 'UUID', '--mountpoint', str(BASE)], text=True).strip() == volume['filesystem_uuid']
    row = next(r for r in json.loads(Path('/opt/toddy-build/config/phase2/sources.lock.json').read_text())['components'] if r['name'] == 'firefox')
    assert row['version'] == '153.2.0esr' and row['sha256'] == 'c443c99704aadaf60fb267d709c42bc283e49e82292084f976369c8327ad833c'
    archive = Path('/mnt/lfs/sources') / row['filename']
    assert not archive.is_symlink() and archive.is_file()
    with archive.open('rb') as stream:
        assert hashlib.file_digest(stream, 'sha256').hexdigest() == row['sha256']
    holder = BASE / 'source'
    assert holder.is_dir() and not holder.is_symlink() and not list(holder.iterdir())
    source = holder / 'firefox-153.2.0'
    state = dict(state='extract-intended', source=row, expanded_bytes=0, members=0,
                 boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip(),
                 volume_uuid=volume['filesystem_uuid'])

    def save():
        with receipt.with_suffix('.part').open('x') as stream:
            json.dump(state, stream, indent=2)
            stream.write('\n')
            stream.flush()
            os.fsync(stream.fileno())
        receipt.with_suffix('.part').replace(receipt)

    save()
    # Stream once; standard data filter rejects escaping links/devices. The
    # upstream '.' entry is omitted to preserve the enclosing directory mode.
    with tarfile.open(archive, mode='r|xz') as bundle:
        for member in bundle:
            parts = PurePosixPath(member.name).parts
            if not parts:
                assert member.isdir()
                continue
            assert not member.name.startswith('/') and '..' not in parts
            assert parts[0] == 'firefox-153.2.0'
            state['members'] += 1
            if member.isfile():
                state['expanded_bytes'] += member.size
            assert state['expanded_bytes'] <= 8 * 1024**3
            bundle.extract(member, holder, filter='data')
    assert all((source / p).is_file() for p in ['mach', 'moz.configure', 'toolkit/moz.configure', 'LICENSE'])
    subprocess.run(['mount', '--bind', str(source), str(source)], check=True)
    subprocess.run(['mount', '-o', 'remount,bind,ro,nosuid,nodev', str(source)], check=True)
    options = subprocess.check_output(['findmnt', '-n', '-o', 'OPTIONS', '--mountpoint', str(source)], text=True).strip().split(',')
    assert {'ro', 'nosuid', 'nodev'} <= set(options)
    vfs = os.statvfs(BASE)
    state.update(state='prepared', source_directory=str(source), source_readonly=True,
                 available_bytes=vfs.f_bavail * vfs.f_frsize,
                 scope='Unmodified frozen source only; configure/compiler/security/ABI/native browser gates pending')
    assert state['available_bytes'] >= 128 * 1024**2
    save()
    print(json.dumps(state))


if __name__ == '__main__':
    main()
