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
subprocess.run([sys.executable, str(VM), 'ssh',
    "if compgen -G '/var/log/toddy/build/*.running.json' > /dev/null; then echo 'Refusing full recipe sync during unfinished build' >&2; exit 1; fi"], check=True)
lock = json.loads((ROOT / 'config/sources.lock.json').read_text())
if lock['status'] != 'verified':
    raise SystemExit('Source lock not verified')
rows = list(lock['packages'])
overlay_path = ROOT / 'config/security-overlay.lock.json'
if overlay_path.exists():
    overlay = json.loads(overlay_path.read_text())
    if overlay['status'] == 'frozen_for_final_build':
        rows += overlay['components']
supplemental_path = ROOT / 'config/supplemental-sources.lock.json'
if supplemental_path.exists():
    supplemental = json.loads(supplemental_path.read_text())
    if supplemental['status'] == 'frozen_for_native_build':
        rows += supplemental['components']
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
references = []
for kind, config_name in [('gcc','compiler-test-reference.json'), ('bash','bash-test-reference.json')]:
    config_path = ROOT/'config'/config_name
    if not config_path.exists():
        continue
    reference = json.loads(config_path.read_text())
    path = ROOT/'.local/references'/(kind+'-reference-'+reference['sha256']+'.log')
    if not path.exists() or hashlib.sha256(path.read_bytes()).hexdigest() != reference['sha256']:
        raise SystemExit('Fetch the pinned '+kind+' reference before syncing build inputs')
    metadata.append('config/'+config_name)
    references.append((kind,path))
if overlay_path.exists():
    metadata.append('config/security-overlay.lock.json')
if supplemental_path.exists():
    metadata.append('config/supplemental-sources.lock.json')
pipe_tar(['-cf', '-'] + metadata,
         'tar --no-overwrite-dir -xf - -C /opt/toddy-build')
# Enumerating files avoids copying the cache directory's mode over sticky sources.
pipe_tar(['-C', '.local/sources', '-cf', '-'] + [r['filename'] for r in rows],
         check + '; tar --no-overwrite-dir -xf - -C /mnt/lfs/sources')
for kind, path in references:
    with path.open('rb') as stream:
        subprocess.run([sys.executable, str(VM), 'ssh', check +
            '; mkdir -p /mnt/lfs/sources/evidence/h07-'+kind+
            '; cat > /mnt/lfs/sources/evidence/h07-'+kind+'/reference.log'],
            stdin=stream, check=True)
print('Build scripts, locks and verified archives transferred; source directory mode preserved.')
