#!/usr/bin/env python3
"""Find private-key armor in a staged tree without disclosing matched bytes.

This is one image audit, not a claim that arbitrary API/account secrets can be
recognized. Public upstream test keys still must stay outside the release root.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import subprocess

BLOCK_SIZE = 64 * 1024
MARKER = re.compile(rb'-----BEGIN (?:(?:RSA |DSA |EC |OPENSSH |ENCRYPTED )?PRIVATE KEY|PGP PRIVATE KEY BLOCK)-----')
OVERLAP = 128


def scan(root):
    root = Path(root)
    if root.is_symlink() or not root.is_dir() or root.resolve() != root:
        raise ValueError('Private-key audit root must be an existing canonical directory')
    findings = []
    files = byte_count = links = special = 0
    device = root.stat().st_dev

    def fail_walk(error):
        raise error

    # Do not follow links into a workstation, mounted build tree or other root.
    # Regular files behind in-tree aliases are visited at their real location.
    for base, directories, names in os.walk(root, followlinks=False, onerror=fail_walk):
        for name in sorted(directories + names):
            path = Path(base) / name
            metadata = path.lstat()
            if stat.S_ISLNK(metadata.st_mode):
                links += 1
                continue
            if metadata.st_dev != device:
                raise ValueError('Staged audit crosses a filesystem boundary')
            if stat.S_ISDIR(metadata.st_mode):
                continue
            if not stat.S_ISREG(metadata.st_mode):
                special += 1
                continue
            digest = hashlib.sha256()
            matched = False
            tail = b''
            with path.open('rb') as stream:
                while chunk := stream.read(BLOCK_SIZE):
                    digest.update(chunk)
                    byte_count += len(chunk)
                    data = tail + chunk
                    matched = matched or bool(MARKER.search(data))
                    tail = data[-OVERLAP:]
            files += 1
            if matched:
                findings.append({'path': '/' + path.relative_to(root).as_posix(),
                                 'reason': 'Private-key armor marker', 'sha256': digest.hexdigest()})
    return {'scope': 'Private-key PEM/OpenSSH/OpenPGP armor markers in staged regular files',
            'regular_files_scanned': files, 'bytes_scanned': byte_count,
            'symlinks_not_followed': links, 'special_nodes_not_read': special,
            'findings': findings, 'matched_contents_disclosed': False,
            'limitations': ['No detection guarantee for arbitrary API tokens, passwords or unarmored/encrypted containers.',
                            'Account state, identity files, package inventory and full image inspection remain separate gates.']}


def main():
    here = Path(__file__).resolve().parent
    subprocess.run(['python3', str(here / 'require_gate.py')], check=True)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('root', type=Path)
    args = parser.parse_args()
    area = Path('/mnt/lfs/sources/stage')
    if args.root == area or not args.root.is_relative_to(area):
        raise ValueError('Select a single designated release staging tree')
    report = scan(args.root)
    print(json.dumps(report, indent=2))
    if report['findings']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
