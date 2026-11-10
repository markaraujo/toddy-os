#!/usr/bin/env python3
"""Keep the historical H11 ISO path and bytes using its verified release twin."""
from pathlib import Path
import fcntl
import hashlib
import json
import os
import shutil
import stat
import subprocess

ROOT = Path(__file__).resolve().parents[2]
RELATIVE = '.local/vm/live-media/h11-6gt6n78r/toddy.iso'
RETAINED = '.local/releases/toddy-foundation-2026-11-07/toddy-foundation-x86_64.iso'
SHA = '4dd9de7a38c4f0d745c2fb74bfdb63e552c372211e5274961814fd9b3d7d22b9'


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def main():
    lock = (ROOT / '.local/vm/native-boot-test.lock').open('a')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    receipt = ROOT / '.local/phase2/h11-iso-copy-custody-1.json'
    assert not receipt.exists() and not receipt.with_suffix('.part').exists(), 'Inspect existing custody; never replay'
    original, retained = ROOT / RELATIVE, ROOT / RETAINED
    link = original.with_name('toddy.iso.custody.part')
    assert not link.exists() and not link.is_symlink()
    for path in (original, retained):
        assert path.resolve() == path and not path.is_symlink()
        assert stat.S_ISREG(path.stat().st_mode) and path.stat().st_uid == os.geteuid()
    before, canonical = original.stat(), retained.stat()
    assert before.st_dev == canonical.st_dev and before.st_ino != canonical.st_ino and before.st_nlink == 1
    assert before.st_size == canonical.st_size == 1095000064 and stat.S_IMODE(canonical.st_mode) == 0o444
    evidence = json.loads((ROOT / 'docs/evidence/H11-artifact-review.json').read_text())
    assert evidence['iso_local_path'] == RELATIVE and evidence['iso_sha256'] == SHA
    assert digest(original) == digest(retained) == SHA
    running = subprocess.check_output(['docker', 'ps', '-q'], text=True).split()
    for identity in running:
        info = json.loads(subprocess.check_output(['docker', 'inspect', identity], text=True))[0]
        if info['Name'].startswith('/toddy-'):
            command = json.dumps([info.get('Args'), info.get('Mounts'), info.get('Path')])
            assert 'h11-6gt6n78r' not in command and str(original) not in command
    # This replica is closed. The immutable release file is never changed.
    opened = subprocess.run(['lsof', '--', str(original)], capture_output=True)
    assert opened.returncode == 1 and not opened.stdout
    state = {'state': 'verified', 'scope': 'One closed byte-identical H11 ISO replica; preserve both original paths, checksums, test evidence, remote release and all VM images',
             'original_path': RELATIVE, 'retained_path': RETAINED, 'sha256': SHA,
             'original_inode': before.st_ino, 'retained_inode': canonical.st_ino,
             'original_allocated_bytes': before.st_blocks * 512,
             'original_mode': stat.S_IMODE(before.st_mode), 'original_mtime_ns': before.st_mtime_ns,
             'bytes': before.st_size, 'host_available_before': shutil.disk_usage(ROOT).free}

    def save():
        part = receipt.with_suffix('.part')
        with part.open('x') as stream:
            stream.write(json.dumps(state, indent=2) + '\n')
            stream.flush()
            os.fsync(stream.fileno())
        part.replace(receipt)

    save()
    assert original.stat().st_ino == before.st_ino and original.stat().st_mtime_ns == before.st_mtime_ns
    assert retained.stat().st_ino == canonical.st_ino and retained.stat().st_mtime_ns == canonical.st_mtime_ns
    state['state'] = 'replace-intended'
    save()
    os.link(retained, link)
    os.replace(link, original)
    assert os.path.samefile(original, retained) and digest(original) == SHA
    state.update(state='complete', host_available_after=shutil.disk_usage(ROOT).free,
                 recovery='If independent file metadata is needed, copy verified retained bytes into a new temporary file, apply original mode/timestamp, atomically replace only the H11 alias. Never edit shared immutable ISO bytes or replay custody.')
    state['reclaimed_bytes'] = state['host_available_after'] - state['host_available_before']
    save()
    print(json.dumps(state))


if __name__ == '__main__':
    main()
