"""Retire one frozen H11 extracted readback duplicate in this candidate only."""
import fcntl
import hashlib
import json
import os
from pathlib import Path
import stat
import subprocess

TARGET = Path('/mnt/lfs')
RECEIPT = Path('/var/log/toddy/phase2/h11-readback-copy-custody-1.json')
SHA = '7a5b454cc9080cc8fe3d28c677688f50acea818da0868e78faf0569323d78b71'
SIZE = 1061642240
ROWS = (
    ('sources/stage/h11-release-media/iso/readback/5', 2142682),
    ('sources/stage/h11-release-compression/rootfs.squashfs', 2014089),
    ('sources/stage/h11-release-media/iso/input/live/rootfs.squashfs', 2115640),
)


def verify(path, inode):
    assert path.resolve() == path and not path.is_symlink()
    assert subprocess.check_output(['findmnt', '-rn', '-o', 'TARGET', '--target', str(path)], text=True).strip() == str(TARGET)
    info = path.stat()
    assert stat.S_ISREG(info.st_mode) and info.st_nlink == 1
    assert info.st_ino == inode and info.st_size == SIZE
    assert info.st_uid == info.st_gid == 0 and info.st_dev == TARGET.stat().st_dev
    with path.open('rb') as stream:
        assert hashlib.file_digest(stream, 'sha256').hexdigest() == SHA
    return {'path': str(path), 'inode': inode, 'bytes': SIZE, 'sha256': SHA}


def no_consumers(path):
    wanted = path.stat()
    for item in Path('/sys/block').glob('loop*/loop/backing_file'):
        text = item.read_text().strip()
        if text:
            candidate = Path('/'+text.lstrip('/'))
            assert candidate.resolve() != path
    for process in Path('/proc').iterdir():
        if not process.name.isdigit():
            continue
        try:
            descriptors = list((process/'fd').iterdir())
        except FileNotFoundError:
            continue
        for descriptor in descriptors:
            try:
                info = descriptor.stat()
            except (FileNotFoundError, ProcessLookupError):
                continue
            assert (info.st_dev, info.st_ino) != (wanted.st_dev, wanted.st_ino), 'Readback cache has an open consumer'


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


def free():
    space = os.statvfs(TARGET)
    return space.f_bavail * space.f_frsize


def main():
    assert os.geteuid() == 0
    subprocess.run(['bash', '-c', 'source /opt/toddy-build/scripts/build/target.sh; guard_target'], check=True)
    assert Path('/proc/sys/kernel/random/boot_id').read_text().strip() == '9ac84ac8-fe0e-41c0-a128-a8e4ad4bebf2'
    assert subprocess.check_output(['findmnt', '-rn', '-o', 'UUID', '--mountpoint', '/mnt/toddy-qt-raster-1'], text=True).strip() == '58e1a631-07a2-40a1-87c2-49de37a69345'
    with open('/var/log/toddy/build/build.lock', 'a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        assert not list(Path('/var/log/toddy/build').glob('*.running.json'))
        assert not Path('/var/log/toddy/build/input-sync.running').exists()
        assert not os.path.lexists(RECEIPT) and not os.path.lexists(RECEIPT.with_suffix('.part'))
        evidence = [verify(TARGET/name, inode) for name, inode in ROWS]
        no_consumers(TARGET/ROWS[0][0])
        before = free()
        record = {'state': 'retire-intended', 'before_free_bytes': before,
                  'retired': evidence[0], 'retained': evidence[1:],
                  'scope': 'One byte-identical H11 extracted ISO readback cache file in candidate overlay only; two full squashfs copies, original ISO, logs and accepted backing remain',
                  'recovery': 'Verify retained compression rootfs SHA256, then copy to a NEW reviewed readback stage. Never replay this custody.'}
        save(record)
        path = TARGET/ROWS[0][0]
        verify(path, ROWS[0][1])
        no_consumers(path)
        path.unlink()
        fd = os.open(path.parent, os.O_DIRECTORY)
        try:
            os.fsync(fd)
        finally:
            os.close(fd)
        for name, inode in ROWS[1:]:
            verify(TARGET/name, inode)
        assert not os.path.lexists(path)
        record.update(state='complete', after_free_bytes=free(), retired_bytes=SIZE)
        assert record['after_free_bytes'] > before
        save(record)
        print(json.dumps(record))


if __name__ == '__main__':
    main()
