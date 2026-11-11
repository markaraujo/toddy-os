#!/usr/bin/env python3
"""Retain one unreferenced cold checkpoint in durable, verified gzip chunks."""
import argparse
import ctypes
import fcntl
import gzip
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

import phase2_compress_cold_checkpoints as cold

CHUNK = 32 * 1024**2
RESERVE = 100 * 1024**3
NAME = 'h07-native-math-builder.qcow2'
PROFILES = {
    'math': ('h07-native-math-builder.qcow2', 'cold-math-chunk-custody-1',
             (11832185, 5940445184, 1793935345557250551)),
    'firefox-capacity': ('h07-gcc-tested-target.qcow2', 'cold-firefox-chunk-custody-1',
                         (11832380, 34298068992, 1793940369084300644)),
    'native-capacity': ('h07-gcc-tested-builder.qcow2', 'cold-native-chunk-custody-1',
                        (11832378, 5949423616, 1793940344780548431)),
}


def save(directory, state):
    part = directory / 'result.json.part'
    with part.open('w') as f:
        json.dump(state, f, indent=2)
        f.write('\n')
        f.flush()
        os.fsync(f.fileno())
    os.replace(part, directory / 'result.json')
    syncdir(directory)


def syncdir(directory):
    fd = os.open(directory, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def punch(fd, offset, size):
    libc = ctypes.CDLL(None, use_errno=True)
    operation = libc.fallocate
    operation.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_longlong, ctypes.c_longlong]
    operation.restype = ctypes.c_int
    if operation(fd, 3, offset, size):  # KEEP_SIZE | PUNCH_HOLE
        raise OSError(ctypes.get_errno(), 'fallocate')
    os.fsync(fd)


def chunk_data(directory, row):
    archive = directory / row['archive']
    assert cold.sha(archive) == row['archive_sha256']
    with gzip.open(archive, 'rb') as f:
        data = f.read(CHUNK + 1)
    assert len(data) == row['bytes']
    assert hashlib.sha256(data).hexdigest() == row['sha256']
    return data


def verify_reconstruction(directory, state, fd):
    h = hashlib.sha256()
    rows = {r['offset']: r for r in state['chunks']}
    for offset in range(0, state['bytes'], CHUNK):
        size = min(CHUNK, state['bytes'] - offset)
        data = chunk_data(directory, rows[offset]) if offset in rows else os.pread(fd, size, offset)
        assert len(data) == size
        h.update(data)
    assert h.hexdigest() == state['source_sha256'], 'Reconstructed original mismatch; preserve everything'


def process(directory, state, fd, reserve=RESERVE, fail_after_verify=False):
    """Resume from verified archive bytes; no unchecked source-range retirement."""
    verify_reconstruction(directory, state, fd)
    rows = {r['offset']: r for r in state['chunks']}
    for offset in range(0, state['bytes'], CHUNK):
        size = min(CHUNK, state['bytes'] - offset)
        row = rows.get(offset)
        if row is None:
            assert shutil.disk_usage(directory).free >= reserve + CHUNK + 64 * 1024**2
            data = os.pread(fd, size, offset)
            assert len(data) == size
            archive = directory / ('chunk-%06d.gz' % (offset // CHUNK))
            # An interrupted unrecorded archive is reconciled against its unchanged source.
            if archive.exists():
                with gzip.open(archive, 'rb') as f:
                    assert f.read(CHUNK + 1) == data
            else:
                part = archive.with_suffix('.part')
                if part.exists():
                    assert part.is_file() and not part.is_symlink()
                    part.unlink()  # Source untouched until a verified durable manifest exists.
                with part.open('xb') as raw:
                    os.fchmod(raw.fileno(), 0o600)
                    with gzip.GzipFile(filename='', fileobj=raw, mode='wb', mtime=0) as f:
                        f.write(data)
                    raw.flush()
                    os.fsync(raw.fileno())
                with gzip.open(part, 'rb') as f:
                    assert f.read(CHUNK + 1) == data
                part.rename(archive)
                syncdir(directory)
            row = {'offset': offset, 'bytes': size, 'sha256': hashlib.sha256(data).hexdigest(),
                   'archive': archive.name, 'archive_sha256': cold.sha(archive), 'state': 'verified'}
            state['chunks'].append(row)
            save(directory, state)
            if fail_after_verify:
                raise InterruptedError('Injected interruption after durable archive verification')
        data = chunk_data(directory, row)
        actual = os.pread(fd, size, offset)
        assert len(actual) == size
        # Reconcile interrupted punch: either original bytes or an already zeroed range.
        assert actual == data or not any(actual), 'Unexpected source change; preserve all inputs'
        if row['state'] == 'retired':
            assert not any(actual), 'Previously retired source changed'
            continue
        if any(actual):
            punch(fd, offset, size)
        assert not any(os.pread(fd, size, offset))
        row['state'] = 'retired'
        save(directory, state)
    verify_reconstruction(directory, state, fd)
    assert os.fstat(fd).st_blocks * 512 < 1024**2
    state.update(state='complete', host_available_after=shutil.disk_usage(directory).free,
                 recovery='Restore chunks in offset order through gzip into the absent original path only with sufficient capacity; verify source_sha256 and bytes before qemu-img check/using the restored backup. Retain chunks until verified. source.custody contains only holes, not a usable image.')
    save(directory, state)


def main():
    global NAME
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--resume', action='store_true')
    parser.add_argument('--profile',choices=PROFILES,default='math')
    args = parser.parse_args()
    root = cold.ROOT
    NAME, context_name, expected = PROFILES[args.profile]
    directory = root / '.local/phase2' / context_name
    source = root / '.local/vm/checkpoints' / NAME
    assert os.geteuid() != 0
    locks = []
    for name in ['.local/vm/native-boot-test.lock', '.local/phase2/cold-checkpoint-compression.lock']:
        lock = open(root / name, 'a')
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        locks.append(lock)
    references, graph = cold.referenced_backings()
    assert NAME not in references
    private = directory / 'source.custody'
    fd = None
    if args.resume:
        state = json.loads((directory / 'result.json').read_text())
        assert state['state'] != 'complete', 'Already complete; never replay'
        assert state.get('profile','math')==args.profile and state['source']==str(source.relative_to(root))
        assert state['producer_sha256'] == cold.sha(Path(__file__))
        if source.exists():
            assert not private.exists() and state['state'] == 'prepared'
            fd = os.open(source, os.O_RDWR | os.O_NOFOLLOW)
            cold.exclusive(fd)
            assert cold.identity(os.fstat(fd)) == state['identity']
            assert cold.sha(source) == state['source_sha256']
            source.rename(private)
            syncdir(source.parent)
            syncdir(directory)
    else:
        assert not directory.exists(), 'Inspect prior receipt, never replay'
        assert source.is_file() and not source.is_symlink() and source.resolve() == source
        fd = os.open(source, os.O_RDWR | os.O_NOFOLLOW)
        original = os.fstat(fd)
        assert original.st_uid == os.geteuid() and original.st_nlink == 1
        assert (original.st_ino,original.st_size,original.st_mtime_ns)==expected
        assert not os.listxattr(source),'Unrecorded extended metadata must remain untouched'
        checked = subprocess.run(['docker', 'run', '--rm', '--user', f'{os.getuid()}:{os.getgid()}',
            '--cap-drop=ALL', '--security-opt=no-new-privileges', '--network=none', '--read-only',
            '-v', str(root / '.local/vm') + ':/vm:ro', 'toddy-qemu:h01',
            'qemu-img', 'check', '/vm/checkpoints/' + NAME], capture_output=True, text=True)
        assert checked.returncode == 0, checked.stderr
        cold.exclusive(fd)
        assert cold.identity(os.fstat(fd)) == cold.identity(original)
        directory.mkdir(mode=0o700)
        state = {'state': 'prepared', 'profile':args.profile,'controller_pid':os.getpid(),'controller_boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip(),'controller_start_ticks':Path('/proc/self/stat').read_text().split()[21], 'source': str(source.relative_to(root)),
                 'bytes': original.st_size, 'identity': cold.identity(original),
                 'source_sha256': cold.sha(source), 'producer_sha256': cold.sha(Path(__file__)),
                 'allocated_before': original.st_blocks * 512, 'chunks': [],
                 'host_available_before': shutil.disk_usage(root).free,
                 'qemu_check_exit': checked.returncode, 'qemu_check_stdout': checked.stdout,
                 'scope': 'Explicit unreferenced cold backup only; exact bytes retained, no active target/backing/master change'}
        (directory / 'graph-before.json').write_text(json.dumps(graph, indent=2) + '\n')
        save(directory, state)
        assert cold.identity(source.stat()) == state['identity']
        source.rename(private)
        syncdir(source.parent)
        syncdir(directory)
    if fd is None:
        fd = os.open(private, os.O_RDWR | os.O_NOFOLLOW)
    try:
        cold.exclusive(fd)
        st = os.fstat(fd)
        assert st.st_ino == state['identity']['inode'] and st.st_size == state['bytes']
        assert st.st_uid == os.geteuid() and st.st_nlink == 1
        assert NAME not in cold.referenced_backings()[0]
        state['state'] = 'compressing'
        save(directory, state)
        process(directory, state, fd)
    finally:
        os.close(fd)
    print(json.dumps({k: state[k] for k in ['state', 'bytes', 'source_sha256', 'host_available_before', 'host_available_after']}))


if __name__ == '__main__':
    main()
