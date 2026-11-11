"""Create one filesystem on the dedicated blank browser virtual disk only."""
from pathlib import Path
import fcntl
import json
import os
import stat
import subprocess
import uuid

SIZE = 16 * 1024**3
SERIAL = 'TODDY-B02-FIREFOX'
WORK = Path('/mnt/lfs/sources/phase2/work/firefox-1')
RECEIPT = Path('/var/log/toddy/phase2/firefox-work-volume-1.json')


def main():
    assert os.geteuid() == 0
    subprocess.run(['bash', '-c', 'source /opt/toddy-build/scripts/build/target.sh; guard_target'], check=True)
    lock = open('/var/log/toddy/build/build.lock', 'a')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    assert not list(Path('/var/log/toddy/build').glob('*.running.json'))
    assert not RECEIPT.exists() and not RECEIPT.with_suffix('.part').exists(), 'Inspect receipt/device; never replay'
    recovery = json.loads(Path('/var/log/toddy/phase2/firefox1-scratch-restored-1.json').read_text())
    assert recovery['state'] == 'complete'
    assert recovery['boot_id'] == Path('/proc/sys/kernel/random/boot_id').read_text().strip()
    devices = [p for p in Path('/sys/class/block').iterdir()
               if (p / 'serial').exists() and (p / 'serial').read_text().strip() == SERIAL]
    assert len(devices) == 1
    sysdev = devices[0]
    assert not (sysdev / 'partition').exists() and not list((sysdev / 'holders').iterdir())
    device = Path('/dev') / sysdev.name
    assert device.resolve() == device and stat.S_ISBLK(device.stat().st_mode)
    assert int((sysdev / 'size').read_text()) * 512 == SIZE
    tree = json.loads(subprocess.check_output(['lsblk', '--json', '-b', '-o', 'NAME,SERIAL,SIZE,TYPE', str(device)], text=True))['blockdevices']
    assert len(tree) == 1 and tree[0]['serial'] == SERIAL and tree[0]['type'] == 'disk'
    assert tree[0]['size'] == SIZE and not tree[0].get('children')
    identity = (sysdev / 'dev').read_text().strip()
    assert all(line.split()[2] != identity for line in Path('/proc/self/mountinfo').read_text().splitlines())
    assert str(device) not in Path('/proc/swaps').read_text()
    signatures = json.loads(subprocess.check_output(['wipefs', '--json', str(device)], text=True))
    assert not signatures.get('signatures'), signatures
    probe = subprocess.run(['blkid', '-p', str(device)], capture_output=True, text=True)
    assert probe.returncode == 2 and not probe.stdout
    fd = os.open(device, os.O_RDONLY | os.O_NOFOLLOW)
    try:
        assert os.pread(fd, 4096, 0) == bytes(4096)
        assert os.pread(fd, 4096, SIZE - 4096) == bytes(4096)
    finally:
        os.close(fd)
    assert not WORK.is_symlink() and (not WORK.exists() or WORK.is_dir() and not list(WORK.iterdir()))
    row = dict(state='filesystem-intended', device=str(device), serial=SERIAL,
               bytes=SIZE, major_minor=identity, filesystem_uuid=str(uuid.uuid4()),
               boot_id=recovery['boot_id'], scope='Dedicated new virtual browser build disk only; not installed root or physical host')

    def save():
        part = RECEIPT.with_suffix('.part')
        with part.open('x') as stream:
            json.dump(row, stream, indent=2)
            stream.write('\n')
            stream.flush()
            os.fsync(stream.fileno())
        part.replace(RECEIPT)
        directory = os.open(RECEIPT.parent, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)

    save()
    # No force, no discard: keep the host allocation and all reserve guarantees.
    result = subprocess.run(['mkfs.ext4', '-m', '0', '-L', 'TODDY_B02_FF',
        '-U', row['filesystem_uuid'], '-E', 'nodiscard,lazy_itable_init=0,lazy_journal_init=0', str(device)],
        capture_output=True, text=True)
    row.update(state='filesystem-command-returned', mkfs_exit=result.returncode,
               mkfs_stdout=result.stdout, mkfs_stderr=result.stderr)
    save()
    assert result.returncode == 0, row
    assert subprocess.check_output(['blkid', '-s', 'UUID', '-o', 'value', str(device)], text=True).strip() == row['filesystem_uuid']
    WORK.mkdir(exist_ok=True)
    subprocess.run(['mount', '-o', 'nosuid,nodev', str(device), str(WORK)], check=True)
    assert subprocess.check_output(['findmnt', '-n', '-o', 'UUID', '--mountpoint', str(WORK)], text=True).strip() == row['filesystem_uuid']
    for name in ['source', 'build', 'stage']:
        directory = WORK / name
        directory.mkdir()
        if name != 'source':
            os.chown(directory, 101, 101)
    vfs = os.statvfs(WORK)
    free = vfs.f_bavail * vfs.f_frsize
    assert free >= 15 * 1024**3
    row.update(state='mounted', work=str(WORK), available_bytes=free,
               source_readonly_isolation='Pending extraction and qualified isolated build setup')
    save()
    print(json.dumps(row))


if __name__ == '__main__':
    main()
