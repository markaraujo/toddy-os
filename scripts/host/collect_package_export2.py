#!/usr/bin/env python3
"""Read-only candidate transfer of exact unsigned export2 assets; no VM writes."""
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
import phase2_candidate_vm as candidate
from mvp_delivery_storage import host_floor

ROOT = Path(__file__).resolve().parents[2]
DESTINATION = ROOT / '.local/phase2/mvp-package-export-2'
SOURCE = '/mnt/lfs/sources/stage/toddy-package-export-2'
RESERVE = 100 * 1024**3 + 512 * 1024**2
HASH = re.compile(r'[a-f0-9]{64}\Z')
FIXED = {'Packages', 'Packages.gz', 'Release', 'archive-keyring.gpg', 'native-trust.json'}


def selected(raw):
    value = json.loads(raw)
    if value.get('kind') != 'unsigned-flat-native-archive-export' or value.get('signed') is not False or value.get('published') is not False:
        raise ValueError('Actual unsigned native export required')
    files = value['files']
    if not isinstance(files, dict) or not FIXED <= files.keys() or len(files) > 1000:
        raise ValueError('Bounded exact native asset set required')
    for name, digest in files.items():
        if not HASH.fullmatch(digest) or (name not in FIXED and not re.fullmatch(r'(?:[a-z0-9+.-]+_[a-f0-9]{64}\.deb|copyright_[a-f0-9]{64}\.txt|source-notices_[a-f0-9]{64}\.json)', name)):
            raise ValueError('Only flat declared public assets allowed')
    for row in value['packages']:
        if files.get(row['asset']) != row['archive_sha256'] or type(row['archive_bytes']) is not int or row['archive_bytes'] <= 0:
            raise ValueError('Exact declared package hash and size required')
    return {**files, 'archive-export.json': hashlib.sha256(raw).hexdigest()}


# Fixed root-owned export path only. No arbitrary guest path/command is accepted.
# This script reads no signing context, credentials or unrelated filesystem tree.
REMOTE = r'''
import hashlib,json,os,pathlib,stat,sys,tarfile
root=pathlib.Path('/mnt/lfs/sources/stage/toddy-package-export-2')
assert root.resolve()==root
for path in (root,root.parent):
 s=path.lstat();assert stat.S_ISDIR(s.st_mode) and s.st_uid==0 and not s.st_mode&0o022
raw=(root/'archive-export.json').read_bytes();assert len(raw)<=16*1024**2
value=json.loads(raw);files=dict(value['files']);files['archive-export.json']=hashlib.sha256(raw).hexdigest()
assert set(p.name for p in root.iterdir())==set(files)
rows={}
for name,digest in sorted(files.items()):
 assert '/' not in name and name not in ('.','..')
 path=root/name;s=path.lstat()
 assert stat.S_ISREG(s.st_mode) and s.st_uid==0 and s.st_nlink==1 and not s.st_mode&0o022
 assert 0<s.st_size<2*1024**3
 with path.open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==digest
 rows[name]={'sha256':digest,'bytes':s.st_size}
if sys.argv[1]=='inventory':
 print(json.dumps({'manifest':value,'manifest_sha256':hashlib.sha256(raw).hexdigest(),'files':rows},sort_keys=True))
elif sys.argv[1]=='stream':
 expected=json.load(sys.stdin);assert expected==rows
 with tarfile.open(fileobj=sys.stdout.buffer,mode='w|') as out:
  for name in sorted(files):out.add(root/name,arcname=name,recursive=False)
else:raise ValueError('fixed action')
'''


def fixed_paths(generation=2):
    if type(generation) is not int or generation not in (2,3,4,5,6,7,8):raise ValueError('Only fixed export2/export3/export4/export5/export6/export7/export8 generations')
    return (SOURCE,DESTINATION) if generation==2 else ('/mnt/lfs/sources/stage/toddy-package-export-'+str(generation),ROOT/('.local/phase2/mvp-package-export-'+str(generation)))


def remote(action,generation=2):
    if action not in ('inventory','stream'):raise ValueError('Only fixed readonly export actions')
    source,_=fixed_paths(generation)
    program=REMOTE.replace(SOURCE,source)
    return candidate.ssh() + ['python3 -I -c ' + shlex.quote(program) + ' ' + action]


def transfer(generation=2):
    source_path,destination=fixed_paths(generation)
    container_id = candidate.owned()
    candidate.bases()
    inventory_raw = subprocess.check_output(remote('inventory',generation), timeout=600)
    if len(inventory_raw) > 24 * 1024**2:
        raise ValueError('Bounded export inventory required')
    inventory = json.loads(inventory_raw)
    # Fetch original bytes separately: JSON serialization is not a receipt digest.
    raw = subprocess.check_output(candidate.ssh() + ['cat ' + source_path + '/archive-export.json'], timeout=60)
    expected = selected(raw)
    rows = inventory['files']
    if inventory['manifest'] != json.loads(raw) or inventory['manifest_sha256'] != hashlib.sha256(raw).hexdigest() or set(rows) != set(expected):
        raise ValueError('Export receipt changed')
    for name, row in rows.items():
        if set(row) != {'sha256', 'bytes'} or row['sha256'] != expected[name] or type(row['bytes']) is not int or not 0 < row['bytes'] < 2 * 1024**3:
            raise ValueError('Exact native asset size/hash required')
    for package in inventory['manifest']['packages']:
        if rows[package['asset']]['bytes'] != package['archive_bytes']:
            raise ValueError('Declared archive byte size changed')
    parent = destination.parent
    if parent.resolve() != parent or not parent.is_dir() or parent.stat().st_uid != os.getuid() or os.path.lexists(destination):
        raise ValueError('New canonical private host destination required')
    if shutil.disk_usage(parent).free < host_floor(generation in (3,4,5,6,7,8)) + sum(row['bytes'] for row in rows.values()) + 1024**2:
        raise ValueError('Preserve selected fixed host reserve plus transfer bytes')
    os.umask(0o077)
    destination.mkdir(mode=0o700)
    assets = destination / 'assets'
    assets.mkdir(mode=0o700)
    process = subprocess.Popen(remote('stream',generation), stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    try:
        process.stdin.write(json.dumps(rows).encode()); process.stdin.close()
        seen = set()
        with tarfile.open(fileobj=process.stdout, mode='r|') as stream:
            for member in stream:
                if member.name not in rows or member.name in seen or not member.isfile() or member.size != rows[member.name]['bytes']:
                    raise ValueError('Unexpected transfer member')
                seen.add(member.name)
                digest = hashlib.sha256()
                with stream.extractfile(member) as source, (assets / member.name).open('xb') as target:
                    os.fchmod(target.fileno(), 0o644)
                    while block := source.read(1024**2):
                        digest.update(block); target.write(block)
                    target.flush(); os.fsync(target.fileno())
                if digest.hexdigest() != rows[member.name]['sha256']:
                    raise ValueError('Transferred asset hash mismatch')
        if process.wait(timeout=60) != 0 or seen != set(rows):
            raise ValueError('Incomplete native transfer')
    finally:
        if process.poll() is None:
            process.kill(); process.wait()
        process.stdout.close()
    if (assets / 'archive-export.json').read_bytes() != raw or candidate.owned() != container_id:
        raise ValueError('Export or owned VM changed')
    receipt = {'version': 1, 'state': 'verified-unsigned-export-transfer', 'source': source_path,
        'archive_export_sha256': hashlib.sha256(raw).hexdigest(), 'files': rows,
        'signed': False, 'published': False, 'native_runtime_qualified': False}
    with (destination / 'verified.json').open('x') as stream:
        json.dump(receipt, stream, sort_keys=True, indent=2); stream.write('\n')
        stream.flush(); os.fsync(stream.fileno())
    for path in (assets, destination):
        fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY)
        try: os.fsync(fd)
        finally: os.close(fd)
    print(json.dumps({'state': receipt['state'], 'destination': str(assets),
        'assets': len(rows), 'bytes': sum(row['bytes'] for row in rows.values()),
        'archive_export_sha256': receipt['archive_export_sha256']}))


if __name__ == '__main__':
    import sys
    if sys.argv[1:]:
        raise SystemExit('No arbitrary source/destination/action arguments')
    transfer()
