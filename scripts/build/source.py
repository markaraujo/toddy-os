#!/usr/bin/env python3
"""Verify the frozen source before any extraction in the designated guest."""
import argparse
import hashlib
import json
from pathlib import Path
import socket
import subprocess
import tarfile
from locked_inputs import locked_source
from source_filter import source_filter, validate_source_members

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('filename')
parser.add_argument('--verify-only', action='store_true')
args = parser.parse_args()
if socket.gethostname() != 'toddy-builder':
    raise SystemExit('Source extraction allowed only in dedicated builder')
mounted = subprocess.run(['findmnt', '-n', '-o', 'SOURCE', '--mountpoint', '/mnt/lfs'],
                         capture_output=True, text=True, check=True).stdout.strip()
if mounted != '/dev/vdb4':
    raise SystemExit('Source target mount mismatch')
root = Path(__file__).resolve().parents[2]
row = locked_source(root, args.filename)
if not row or Path(args.filename).name != args.filename:
    raise SystemExit('Unknown/unsafe source')
archive = Path('/mnt/lfs/sources') / args.filename
with archive.open('rb') as stream:
    actual = hashlib.file_digest(stream, 'sha256').hexdigest()
if actual != row['sha256']:
    raise SystemExit('Frozen source SHA-256 mismatch: not extracted')
print(f'VERIFIED {args.filename} {actual}', flush=True)
if not args.verify_only:
    destination = Path.cwd().resolve()
    if not destination.is_relative_to(Path('/mnt/lfs/sources')):
        raise SystemExit('Extraction outside target sources rejected')
    with tarfile.open(archive) as source:
        validate_source_members(args.filename, source.getmembers())
        roots = {Path(member.name).parts[0] for member in source.getmembers() if Path(member.name).parts}
        if any((destination / name).exists() for name in roots):
            raise SystemExit('Existing source tree: inspect/clean before rebuilding')
        checked_filter = source_filter(args.filename)
        # Reject unsafe members before creating even a partial source tree.
        for member in source.getmembers():
            checked_filter(member, destination)
        source.extractall(destination, filter=checked_filter)
