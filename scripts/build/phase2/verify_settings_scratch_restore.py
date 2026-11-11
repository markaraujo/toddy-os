#!/usr/bin/env python3
"""Verify restored cache bytes, metadata and exact hardlink equivalence classes."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import stat


def verify(root, receipt, restore_times=False):
    rows = [r for r in receipt['inventory'] if r['type'] != 'stale-socket']
    expected = {r['path']: r for r in rows}
    actual = set()
    for base, directories, files in os.walk(root, followlinks=False):
        actual.update(str((Path(base)/name).relative_to(root)) for name in directories+files)
    assert actual == set(expected), 'Restored path set mismatch'
    original_to_restored = {}
    restored_to_original = {}
    for name, row in expected.items():
        path = root / name
        assert not Path(name).is_absolute() and '..' not in Path(name).parts
        if restore_times:
            os.utime(path, ns=(row['mtime_ns'], row['mtime_ns']), follow_symlinks=False)
        s = path.lstat()
        assert s.st_mode == row['mode'] and s.st_uid == row['uid'] and s.st_gid == row['gid'], name
        assert s.st_mtime_ns == row['mtime_ns'], name
        if row['type'] == 'file':
            assert stat.S_ISREG(s.st_mode) and s.st_size == row['bytes'], name
            with path.open('rb') as f:
                assert hashlib.file_digest(f, 'sha256').hexdigest() == row['sha256'], name
            original = tuple(row['hardlink_identity'])
            restored = (s.st_dev, s.st_ino)
            assert original_to_restored.setdefault(original, restored) == restored, name
            assert restored_to_original.setdefault(restored, original) == original, name
        elif row['type'] == 'symlink':
            assert stat.S_ISLNK(s.st_mode) and os.readlink(path) == row['target'], name
        else:
            assert row['type'] == 'directory' and stat.S_ISDIR(s.st_mode), name
    return {'state': 'complete', 'verified_entries': len(rows),
            'verified_distinct_regular_inodes': len(original_to_restored),
            'exact_bytes_modes_owners_timestamps_symlinks_hardlinks': True}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('root', type=Path)
    p.add_argument('receipt', type=Path)
    p.add_argument('--restore-times', action='store_true')
    a = p.parse_args()
    print(json.dumps(verify(a.root, json.loads(a.receipt.read_text()), a.restore_times)))


if __name__ == '__main__':
    main()
