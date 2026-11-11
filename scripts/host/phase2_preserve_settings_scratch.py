#!/usr/bin/env python3
"""Archive the existing boot-scoped Samba/Settings cache before any cold VM test."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tarfile

import phase2_vm

ROOT = phase2_vm.ROOT
CONTEXT = ROOT / '.local/phase2/settings-scratch-custody-1'
GUEST = r'''
import fcntl,hashlib,json,os,stat,subprocess,sys
from pathlib import Path
root=Path('/run/toddy-samba-client-1')
assert Path('/proc/sys/kernel/random/boot_id').read_text().strip()==expected_boot
lock=open('/var/log/toddy/build/build.lock','a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
assert not list(Path('/var/log/toddy/build').glob('*.running.json'))
subprocess.run(['bash','-c','source /opt/toddy-build/scripts/build/target.sh; guard_target'],check=True,stdout=sys.stderr)
mounts=json.loads(subprocess.check_output(['findmnt','--json','--list','-o','ID,TARGET,SOURCE,FSTYPE,OPTIONS'],text=True))['filesystems']
selected=[r for r in mounts if r['source'].startswith('toddy-samba-client-1')]
assert any(r['target']==str(root) and r['fstype']=='tmpfs' for r in selected)
assert os.statvfs(root).f_blocks*os.statvfs(root).f_frsize==2*1024**3
if generation==1:assert expected_boot=='0933ee87-f0bc-4074-9491-8b4e6892121f' and any(r['target']==str(root) and r['id']==580 for r in selected)
else:
 recovery=json.loads(Path('/var/log/toddy/phase2/localsearch4-scratch-restored-1.json').read_text());assert recovery['state']=='complete' and recovery['boot_id']==expected_boot
 assert Path('/var/log/toddy/phase2/nautilus-1.exit').read_text().strip()=='0'
 for name in ['b02-localsearch-install','b02-localsearch-schema-union-install']:
  r=json.loads(Path('/var/log/toddy/build',name+'.success.json').read_text());assert r['recipe_exit']==r['postcheck_exit']==0
# No live fixture process is allowed. Old sockets have no restorable contents.
processes=subprocess.check_output(['ps','-eo','pid,args'],text=True)
assert not any('smbd --foreground' in s or 'smbd -F' in s for s in processes.splitlines())
def inventory():
 rows=[]
 for base,dirs,files in os.walk(root,followlinks=False):
  for name in sorted(dirs+files):
   p=Path(base)/name;s=p.lstat();r={'path':str(p.relative_to(root)),'mode':s.st_mode,'uid':s.st_uid,'gid':s.st_gid,'mtime_ns':s.st_mtime_ns}
   if stat.S_ISREG(s.st_mode):
    r.update(type='file',bytes=s.st_size,sha256=hashlib.file_digest(p.open('rb'),'sha256').hexdigest(),hardlink_identity=[s.st_dev,s.st_ino])
   elif stat.S_ISDIR(s.st_mode):r['type']='directory'
   elif stat.S_ISLNK(s.st_mode):r.update(type='symlink',target=os.readlink(p))
   elif stat.S_ISSOCK(s.st_mode):r['type']='stale-socket'
   else:raise AssertionError('Unexpected special file: '+str(p))
   rows.append(r)
 return sorted(rows,key=lambda r:r['path'])
before=inventory()
receipt=Path('/var/log/toddy/phase2')/('settings-scratch-custody-'+str(generation)+'.json')
assert not receipt.exists(),'Inspect archive and receipt; never replay custody'
if generation==2:
 old=json.loads(Path('/var/log/toddy/phase2/settings-scratch-custody-1.json').read_text());assert old['state']=='archive-stream-complete-source-unchanged'
 current={r['path']:r for r in before};forward={};reverse={}
 for row in old['inventory']:
  if row['type']=='stale-socket':continue
  actual=current[row['path']]
  assert {k:v for k,v in row.items() if k!='hardlink_identity'}=={k:v for k,v in actual.items() if k!='hardlink_identity'},row['path']
  if row['type']=='file':
   origin=tuple(row['hardlink_identity']);restored=tuple(actual['hardlink_identity'])
   assert forward.setdefault(origin,restored)==restored and reverse.setdefault(restored,origin)==origin
state={'state':'archiving','boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip(),'mounts':selected,'generation':generation,'prior_generation_files_metadata_and_hardlinks_unchanged':generation==2,'inventory':before,'scope':'Preserve all regular source/compiler/stage/fixture-result bytes and symlinks/hardlinks; stale sockets have no restorable payload. No guest files removed or builder stopped.'}
receipt.write_text(json.dumps(state,indent=2)+'\n')
sockets=[r['path'] for r in before if r['type']=='stale-socket']
cmd=['tar','--create','--gzip','--file=-','--numeric-owner','--acls','--xattrs','--sparse','--one-file-system']
cmd += ['--exclude=./'+p for p in sockets]
cmd += ['-C',str(root),'.']
r=subprocess.run(cmd)
assert r.returncode==0
assert inventory()==before,'Scratch changed during custody; preserve archive as unaccepted'
state['state']='archive-stream-complete-source-unchanged'
receipt.write_text(json.dumps(state,indent=2)+'\n')
'''


def main():
    global CONTEXT
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--generation',type=int,choices=[1,2],default=1)
    args=parser.parse_args()
    CONTEXT=ROOT/'.local/phase2'/('settings-scratch-custody-'+str(args.generation))
    assert not CONTEXT.exists(), 'Inspect existing archive/guest receipt before any replay'
    assert shutil.disk_usage(ROOT).free >= 100 * 1024**3 + 1536 * 1024**2
    CONTEXT.mkdir(mode=0o700)
    archive = CONTEXT / 'scratch.tar.gz'
    with archive.open('xb') as output, (CONTEXT / 'guest.log').open('xb') as log:
        os.fchmod(output.fileno(), 0o600)
        expected_boot=subprocess.check_output(phase2_vm.ssh_args()+['cat /proc/sys/kernel/random/boot_id'],text=True).strip()
        body='generation='+repr(args.generation)+'\nexpected_boot='+repr(expected_boot)+'\n'+GUEST
        result = subprocess.run(phase2_vm.ssh_args() + ['python3 -'], input=body.encode(), stdout=output, stderr=log)
        output.flush()
        os.fsync(output.fileno())
    assert result.returncode == 0, 'Preserve partial archive and inspect guest receipt; no replay'
    receipt = subprocess.check_output(phase2_vm.ssh_args() + ['cat /var/log/toddy/phase2/settings-scratch-custody-'+str(args.generation)+'.json'])
    (CONTEXT / 'guest-receipt.json').write_bytes(receipt)
    state = json.loads(receipt)
    assert state['state'] == 'archive-stream-complete-source-unchanged'
    expected = {r['path']: r for r in state['inventory'] if r['type'] != 'stale-socket'}
    found = set()
    links = []
    with tarfile.open(archive, 'r:gz') as tar:
        for member in tar:
            name = member.name.removeprefix('./').rstrip('/')
            if not name or name == '.':
                continue
            assert name in expected and name not in found, name
            found.add(name)
            row = expected[name]
            assert member.uid == row['uid'] and member.gid == row['gid']
            assert member.mode == row['mode'] & 0o7777
            if member.islnk():
                assert row['type'] == 'file'
                links.append((name, member.linkname.removeprefix('./')))
            elif member.isfile():
                assert row['type'] == 'file' and member.size == row['bytes']
                assert hashlib.file_digest(tar.extractfile(member), 'sha256').hexdigest() == row['sha256']
            elif member.isdir():
                assert row['type'] == 'directory'
            elif member.issym():
                assert row['type'] == 'symlink' and member.linkname == row['target']
            else:
                raise AssertionError('Unexpected archive member')
    assert found == set(expected)
    for name, target in links:
        assert expected[name]['hardlink_identity'] == expected[target]['hardlink_identity']
        assert expected[name]['sha256'] == expected[target]['sha256']
    result = {'state': 'complete', 'generation':args.generation,'prior_generation_files_metadata_and_hardlinks_unchanged':state.get('prior_generation_files_metadata_and_hardlinks_unchanged',False), 'archive_sha256': hashlib.file_digest(archive.open('rb'), 'sha256').hexdigest(),
              'archive_bytes': archive.stat().st_size, 'verified_entries': len(found), 'verified_hardlinks': len(links),
              'stale_sockets_omitted': sum(r['type']=='stale-socket' for r in state['inventory']),
              'guest_receipt_sha256': hashlib.sha256(receipt).hexdigest(),
              'host_available_after': shutil.disk_usage(ROOT).free,
              'recovery': 'Verify archive SHA, restore into the same fresh 2 GiB tmpfs with numeric ownership/ACL/xattrs/sparse/hardlinks, compare all file hashes and symlink targets to guest-receipt.json before remounting the recorded exact bind aliases. Do not replay source preparation, compiler jobs, fixtures or package transactions.'}
    assert result['host_available_after'] >= 100*1024**3
    (CONTEXT / 'result.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result))


if __name__ == '__main__':
    main()
