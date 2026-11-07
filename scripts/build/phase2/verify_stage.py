#!/usr/bin/env python3
"""Conservative Phase 2 stage validation; no absolute/escaping links or privilege."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import stat


def inspect_stage(root):
    if root.is_symlink() or not root.is_dir():
        raise ValueError('Stage must be a real directory')
    root = root.resolve()
    manifest = {}
    for base, dirs, files in os.walk(root, followlinks=False):
        for name in sorted(dirs + files):
            path = Path(base) / name
            relative = path.relative_to(root).as_posix()
            if any(ord(c) < 32 for c in relative):
                raise ValueError('Control character in stage path')
            st = path.lstat()
            mode = stat.S_IMODE(st.st_mode)
            if mode & 0o6000 or (not path.is_symlink() and mode & 0o002):
                raise ValueError('Privileged/world-writable stage entry: ' + relative)
            if os.listxattr(path, follow_symlinks=False):
                raise ValueError('Undeclared staged extended attributes: ' + relative)
            row = {'mode': mode}
            if stat.S_ISLNK(st.st_mode):
                link = os.readlink(path)
                if Path(link).is_absolute() or not path.resolve().is_relative_to(root):
                    raise ValueError('Absolute/escaping staged link: ' + relative)
                if not path.exists():
                    raise ValueError('Unresolved staged link needs declared dependency: ' + relative)
                row['symlink'] = link
            elif stat.S_ISDIR(st.st_mode):
                row['directory'] = True
            elif stat.S_ISREG(st.st_mode):
                with path.open('rb') as stream:
                    row['sha256'] = hashlib.file_digest(stream, 'sha256').hexdigest()
                row['bytes'] = st.st_size
            else:
                raise ValueError('Special staged file: ' + relative)
            manifest[relative] = row
    if not manifest:
        raise ValueError('Empty stage')
    encoded = json.dumps(manifest, sort_keys=True, separators=(',', ':')).encode()
    return {'manifest_sha256': hashlib.sha256(encoded).hexdigest(), 'entries': manifest}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('stage', type=Path)
    args = parser.parse_args()
    print(json.dumps(inspect_stage(args.stage), indent=2))
