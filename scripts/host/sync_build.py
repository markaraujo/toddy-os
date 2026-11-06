#!/usr/bin/env python3
"""Copy only build scripts, locks and verified archives into the guarded guest."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
VM = ROOT / 'scripts/host/vm.py'
check = 'source /opt/toddy-build/scripts/build/target.sh; guard_target'
subprocess.run([sys.executable, str(VM), 'ssh', check], check=True)
lock = json.loads((ROOT / 'config/sources.lock.json').read_text())
if lock['status'] != 'verified':
    raise SystemExit('Source lock not verified')
rows = list(lock['packages'])
overlay_path = ROOT / 'config/security-overlay.lock.json'
if overlay_path.exists():
    overlay = json.loads(overlay_path.read_text())
    if overlay['status'] == 'frozen_for_final_build':
        rows += overlay['components']
for row in rows:
    path = ROOT / '.local/sources' / row['filename']
    with path.open('rb') as stream:
        actual = hashlib.file_digest(stream, 'sha256').hexdigest()
    if actual != row['sha256']:
        raise SystemExit(f'Source mismatch before transfer: {row["filename"]}')


def pipe_tar(args, remote):
    sender = subprocess.Popen(['tar', *args], cwd=ROOT, stdout=subprocess.PIPE)
    try:
        result = subprocess.run([sys.executable, str(VM), 'ssh', remote], stdin=sender.stdout)
    finally:
        sender.stdout.close()
    sender_code = sender.wait()
    if sender_code or result.returncode:
        raise SystemExit(f'Transfer failed: sender={sender_code}, receiver={result.returncode}')


metadata = ['scripts/build', 'LICENSES', 'config/component-licenses.json', 'config/books.lock.json', 'config/sources.lock.json']
if overlay_path.exists():
    metadata.append('config/security-overlay.lock.json')
pipe_tar(['-cf', '-'] + metadata,
         'tar --no-overwrite-dir -xf - -C /opt/toddy-build')
# Enumerating files avoids copying the cache directory's mode over sticky sources.
pipe_tar(['-C', '.local/sources', '-cf', '-'] + [r['filename'] for r in rows],
         check + '; tar --no-overwrite-dir -xf - -C /mnt/lfs/sources')
print('Build scripts, locks and verified archives transferred; source directory mode preserved.')
