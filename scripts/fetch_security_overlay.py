#!/usr/bin/env python3
"""Fetch selected SHA-pinned security or supplemental additions; never extract."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--supplemental', action='store_true')
args=parser.parse_args()
filename='supplemental-sources.lock.json' if args.supplemental else 'security-overlay.lock.json'
required='frozen_for_native_build' if args.supplemental else 'frozen_for_final_build'
lock=json.loads((ROOT/'config'/filename).read_text())
if lock['status'] != required:
    raise SystemExit('No selected frozen additions')
folder=ROOT/'.local/sources'
folder.mkdir(parents=True,exist_ok=True)
for row in lock['components']:
    name=row['filename']
    if Path(name).name != name or name in ('.','..'):
        raise SystemExit('Unsafe frozen input filename')
    path=folder/name
    if not path.exists():
        part=path.with_name(name+'.part')
        subprocess.run(['curl','-fLsS','--retry','3',row['url'],'-o',str(part)],check=True)
        with part.open('rb') as f: actual=hashlib.file_digest(f,'sha256').hexdigest()
        if actual != row['sha256']: raise SystemExit('Frozen input integrity mismatch')
        part.replace(path)
    with path.open('rb') as f: actual=hashlib.file_digest(f,'sha256').hexdigest()
    if actual != row['sha256']: raise SystemExit('Cached frozen input mismatch')
    print(f'VERIFIED {name} {actual}')
