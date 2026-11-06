#!/usr/bin/env python3
"""Fetch the exact official compiler-test reference as data, never execute it."""
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
config = json.loads((ROOT / 'config/compiler-test-reference.json').read_text())
folder = ROOT / '.local/references'
folder.mkdir(parents=True, exist_ok=True)
path = folder / ('gcc-reference-' + config['sha256'] + '.log')
if not path.exists():
    part = path.with_suffix('.part')
    subprocess.run(['curl', '-fLsS', '--retry', '3', config['url'], '-o', str(part)], check=True)
    if hashlib.sha256(part.read_bytes()).hexdigest() != config['sha256']:
        raise SystemExit('Official compiler reference changed; reject before using results')
    part.replace(path)
if hashlib.sha256(path.read_bytes()).hexdigest() != config['sha256']:
    raise SystemExit('Cached official compiler reference corrupted')
print('VERIFIED official GCC test reference ' + config['sha256'])
