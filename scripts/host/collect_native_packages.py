#!/usr/bin/env python3
"""Copy verified native archives/metadata outside Git without stopping a build.

This is a partial package recovery cache, not a bootable system checkpoint.
The guest exporter verifies provenance first; downloaded bytes are verified again.
"""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import shlex
import subprocess
import tarfile
import vm

ROOT = Path(__file__).resolve().parents[2]
parent = ROOT/'.local/native-package-snapshots'
parent.mkdir(parents=True, exist_ok=True)
if parent.is_symlink() or parent.resolve() != parent:
    raise SystemExit('Package snapshot destination must stay in real project-local storage')
destination = parent/datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
destination.mkdir()
inventory_path = destination/'inventory.json'
with inventory_path.open('wb') as stream:
    subprocess.run(vm.ssh_args()+['python3 /opt/toddy-build/scripts/build/export_inventory.py'],
                   stdout=stream, check=True)
inventory = json.loads(inventory_path.read_text())
paths = []
for row in inventory['components']:
    name = row['archive']
    if not re.fullmatch(r'[a-z0-9+.-]+_[0-9A-Za-z.+:~_-]+_(amd64|all)\.deb', name):
        raise SystemExit('Unsafe native archive filename')
    paths += ['var/cache/toddy/packages/'+name,
              'var/log/toddy/packages/'+name.removesuffix('.deb')+'.json']
archive = destination/'native-packages.tar.gz'
with archive.open('wb') as stream:
    command = 'tar -C / -czf - '+shlex.join(paths)
    subprocess.run(vm.ssh_args()+[command], stdout=stream, check=True)
with tarfile.open(archive) as stream:
    # Only the requested regular metadata/archive files may cross this boundary.
    members = stream.getmembers()
    if {m.name for m in members} != set(paths) or any(not m.isfile() for m in members):
        raise SystemExit('Unexpected native package snapshot member')
    stream.extractall(destination, filter='data')

def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream,'sha256').hexdigest()

for row in inventory['components']:
    name = row['archive']
    if digest(destination/'var/cache/toddy/packages'/name) != row['archive_sha256']:
        raise SystemExit('Copied native archive hash mismatch')
    metadata = destination/'var/log/toddy/packages'/(name.removesuffix('.deb')+'.json')
    if digest(metadata) != row['component_record_sha256']:
        raise SystemExit('Copied component record hash mismatch')
record = {'package_count':inventory['package_count'], 'release_complete':False,
          'inventory_sha256':digest(inventory_path), 'archive_sha256':digest(archive),
          'scope':'Verified native package cache only; not a system checkpoint'}
(destination/'verified.json').write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps({'destination':str(destination.relative_to(ROOT)), **record}))
