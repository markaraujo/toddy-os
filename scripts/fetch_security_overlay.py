#!/usr/bin/env python3
"""Fetch only selected, SHA-pinned security additions; never extract them."""
import hashlib
import json
from pathlib import Path
import subprocess

ROOT=Path(__file__).resolve().parents[1]
lock=json.loads((ROOT/'config/security-overlay.lock.json').read_text())
if lock['status'] != 'frozen_for_final_build':
    raise SystemExit('No selected final security overlay')
folder=ROOT/'.local/sources'
folder.mkdir(parents=True,exist_ok=True)
for row in lock['components']:
    name=row['filename']
    if Path(name).name != name or name in ('.','..'):
        raise SystemExit('Unsafe security input filename')
    path=folder/name
    if not path.exists():
        part=path.with_name(name+'.part')
        subprocess.run(['curl','-fLsS','--retry','3',row['url'],'-o',str(part)],check=True)
        with part.open('rb') as f: actual=hashlib.file_digest(f,'sha256').hexdigest()
        if actual != row['sha256']: raise SystemExit('Security input integrity mismatch')
        part.replace(path)
    with path.open('rb') as f: actual=hashlib.file_digest(f,'sha256').hexdigest()
    if actual != row['sha256']: raise SystemExit('Cached security input mismatch')
    print(f'VERIFIED {name} {actual}')
