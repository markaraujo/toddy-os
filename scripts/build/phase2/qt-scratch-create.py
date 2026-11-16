#!/usr/bin/env python3
"""Initialize only the new, blank candidate Qt scratch disk, exactly once."""
import fcntl
import json
import os
from pathlib import Path
import subprocess
import time

DEVICE = '/dev/vdc'
MOUNT = Path('/mnt/toddy-qt-raster-1')
RECEIPT = Path('/var/log/toddy/build/qt-scratch-create.json')


def run(*args):
    return subprocess.check_output(args, text=True).strip()


def save(value):
    part = RECEIPT.with_suffix('.part')
    with part.open('x') as stream:
        json.dump(value, stream, indent=2)
        stream.write('\n')
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(part, RECEIPT)
    fd = os.open(RECEIPT.parent, os.O_DIRECTORY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def main():
    assert os.geteuid() == 0
    subprocess.run(['bash', '-c', 'source /opt/toddy-build/scripts/build/target.sh; guard_target'], check=True)
    with open('/var/log/toddy/build/build.lock', 'a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        assert not list(RECEIPT.parent.glob('*.running.json'))
        assert not (RECEIPT.parent/'input-sync.running').exists()
        assert not os.path.lexists(RECEIPT) and not os.path.lexists(RECEIPT.with_suffix('.part'))
        assert not os.path.lexists(MOUNT)
        assert run('lsblk', '-dn', '-o', 'SERIAL', DEVICE) == 'TODDY-QT-RASTER-1'
        assert run('blockdev', '--getsize64', DEVICE) == str(16 * 1024**3)
        disk = json.loads(run('lsblk', '-J', '-o', 'PATH,TYPE,MOUNTPOINTS', DEVICE))['blockdevices']
        assert len(disk) == 1 and disk[0]['path'] == DEVICE and disk[0]['type'] == 'disk'
        assert not disk[0].get('children') and not any(disk[0]['mountpoints'])
        assert json.loads(run('wipefs', '--json', DEVICE))['signatures'] == []
        state = {'state': 'format-intended', 'device': DEVICE, 'serial': 'TODDY-QT-RASTER-1',
                 'bytes': 16*1024**3, 'created_ns': time.time_ns()}
        save(state)
        subprocess.run(['mkfs.ext4', '-m', '0', '-L', 'TODDY_QT_WORK', DEVICE], check=True)
        state.update(state='formatted', uuid=run('blkid', '-s', 'UUID', '-o', 'value', DEVICE))
        save(state)
        MOUNT.mkdir(mode=0o755)
        subprocess.run(['mount', '-o', 'rw,nosuid,nodev', DEVICE, str(MOUNT)], check=True)
        assert run('findmnt', '-rn', '-o', 'SOURCE', '--mountpoint', str(MOUNT)) == DEVICE
        assert run('findmnt', '-rn', '-o', 'FSTYPE', '--mountpoint', str(MOUNT)) == 'ext4'
        assert {'rw', 'nosuid', 'nodev'} <= set(run('findmnt', '-rn', '-o', 'OPTIONS', '--mountpoint', str(MOUNT)).split(','))
        fs = os.statvfs(MOUNT)
        free = fs.f_bavail * fs.f_frsize
        assert free >= 12*1024**3
        state.update(state='mounted', available_bytes=free, filesystem_created=True)
        save(state)
        print(json.dumps(state))


if __name__ == '__main__':
    main()
