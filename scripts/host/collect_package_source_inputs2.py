#!/usr/bin/env python3
"""Read-only custody of exact export2 native records/catalog proof for host sources."""
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import shutil
import subprocess
import sys
import tarfile

sys.path.insert(0, str(Path(__file__).resolve().parent))
import collect_package_export2 as transfer

DESTINATION = transfer.DESTINATION / 'source-inputs'
REMOTE = r'''
import hashlib,json,pathlib,stat,sys,tarfile
root=pathlib.Path('/mnt/lfs/sources/stage/toddy-package-export-2')
raw=(root/'archive-export.json').read_bytes()
assert hashlib.sha256(raw).hexdigest()==sys.argv[1]
value=json.loads(raw);paths={}
for row in value['packages']:
 name=row['name']+'_'+row['version']+'_'+row['architecture']+'.json'
 assert '/' not in name
 paths['records/'+name]=(pathlib.Path('/var/log/toddy/packages')/name,row['component_record_sha256'])
base=pathlib.Path('/mnt/lfs/sources/stage/toddy-optional-projection-1')
projection=(base/'optional-projection.json').read_bytes()
assert hashlib.sha256(projection).hexdigest()==value['inputs']['optional-projection.json']
paths['optional-projection.json']=(base/'optional-projection.json',value['inputs']['optional-projection.json'])
paths['generated-catalog-attestation.json']=(base/'generated-catalog-attestation.json',json.loads(projection)['generated_catalog_attestation_sha256'])
rows={}
for name,(path,sha) in sorted(paths.items()):
 assert path.resolve()==path
 s=path.lstat();assert stat.S_ISREG(s.st_mode) and s.st_uid==0 and s.st_nlink==1 and not s.st_mode&0o022
 assert 0<s.st_size<128*1024**2
 with path.open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==sha
 rows[name]={'sha256':sha,'bytes':s.st_size}
if sys.argv[2]=='inventory':print(json.dumps(rows,sort_keys=True))
elif sys.argv[2]=='stream':
 assert json.load(sys.stdin)==rows
 with tarfile.open(fileobj=sys.stdout.buffer,mode='w|') as out:
  for name,(path,sha) in sorted(paths.items()):out.add(path,arcname=name,recursive=False)
else:raise ValueError('Fixed read-only action')
'''


def run():
    candidate = transfer.candidate
    identity = candidate.owned()
    candidate.bases()
    parent = transfer.DESTINATION
    raw = (parent / 'assets/archive-export.json').read_bytes()
    manifest = json.loads(raw)
    digest = hashlib.sha256(raw).hexdigest()
    if json.loads((parent / 'verified.json').read_bytes())['archive_export_sha256'] != digest:
        raise ValueError('Complete verified export transfer required')
    paths = {}
    for row in manifest['packages']:
        stem = row['name'] + '_' + row['version'] + '_' + row['architecture'] + '.json'
        if not re.fullmatch(r'[a-z0-9+.-]+_[0-9A-Za-z.+:~_-]+_(?:amd64|all)\.json', stem):
            raise ValueError('Exact flat native record identity required')
        paths['records/' + stem] = row['component_record_sha256']
    def remote(action):
        return candidate.ssh() + ['python3 -I -c ' + shlex.quote(REMOTE) + ' ' + digest + ' ' + action]
    rows = json.loads(subprocess.check_output(remote('inventory'), timeout=180))
    expected_names = set(paths) | {'optional-projection.json', 'generated-catalog-attestation.json'}
    if set(rows) != expected_names:
        raise ValueError('Exact referenced native record/proof set required')
    paths['optional-projection.json'] = manifest['inputs']['optional-projection.json']
    for name, row in rows.items():
        if set(row) != {'sha256', 'bytes'} or not transfer.HASH.fullmatch(row['sha256']) or type(row['bytes']) is not int or not 0 < row['bytes'] < 128 * 1024**2 or (name in paths and row['sha256'] != paths[name]):
            raise ValueError('Bounded actual source metadata hash/size required')
    if os.path.lexists(DESTINATION) or parent.resolve() != parent or shutil.disk_usage(parent).free < transfer.RESERVE + sum(row['bytes'] for row in rows.values()) + 1024**2:
        raise ValueError('New private metadata destination and host reserve required')
    os.umask(0o077)
    DESTINATION.mkdir(mode=0o700)
    (DESTINATION / 'records').mkdir(mode=0o700)
    process = subprocess.Popen(remote('stream'), stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    try:
        process.stdin.write(json.dumps(rows).encode()); process.stdin.close()
        seen = set()
        with tarfile.open(fileobj=process.stdout, mode='r|') as stream:
            for member in stream:
                if member.name not in rows or member.name in seen or not member.isfile() or member.size != rows[member.name]['bytes']:
                    raise ValueError('Unexpected source metadata member')
                seen.add(member.name)
                sha = hashlib.sha256()
                with stream.extractfile(member) as source, (DESTINATION / member.name).open('xb') as target:
                    while block := source.read(1024**2):
                        sha.update(block); target.write(block)
                    target.flush(); os.fsync(target.fileno())
                if sha.hexdigest() != rows[member.name]['sha256']:
                    raise ValueError('Source metadata transfer hash mismatch')
        if process.wait(timeout=60) != 0 or seen != expected_names or candidate.owned() != identity:
            raise ValueError('Incomplete source metadata custody')
    finally:
        if process.poll() is None:
            process.kill(); process.wait()
        process.stdout.close()
    projection = json.loads((DESTINATION / 'optional-projection.json').read_bytes())
    if projection['generated_catalog_attestation_sha256'] != rows['generated-catalog-attestation.json']['sha256']:
        raise ValueError('Catalog export proof chain mismatch')
    receipt = {'version': 1, 'state': 'verified-native-source-input-transfer',
        'archive_export_sha256': digest, 'files': rows, 'qualification_created': False}
    with (DESTINATION / 'verified.json').open('x') as target:
        json.dump(receipt, target, indent=2, sort_keys=True); target.write('\n')
        target.flush(); os.fsync(target.fileno())
    for directory in (DESTINATION / 'records', DESTINATION, parent):
        fd = os.open(directory, os.O_RDONLY | os.O_DIRECTORY)
        try: os.fsync(fd)
        finally: os.close(fd)
    print(json.dumps({'state': receipt['state'], 'files': len(rows), 'bytes': sum(row['bytes'] for row in rows.values()), 'destination': str(DESTINATION)}))


if __name__ == '__main__':
    if sys.argv[1:]:
        raise SystemExit('Fixed source inputs only; no arbitrary guest command/path')
    run()
