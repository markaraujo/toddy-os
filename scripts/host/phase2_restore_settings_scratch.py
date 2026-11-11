#!/usr/bin/env python3
"""Restore the exact qualified boot-scoped cache and its recorded bind aliases."""
import argparse
import re
import hashlib
import json
from pathlib import Path
import shlex
import shutil
import subprocess

import phase2_vm

ROOT=phase2_vm.ROOT
CONTEXT=ROOT/'.local/phase2/settings-scratch-custody-1'
GUEST=r'''
import fcntl,hashlib,json,os,shutil,subprocess,sys
from pathlib import Path
subprocess.run(['bash','-c','source /opt/toddy-build/scripts/build/target.sh; guard_target'],check=True)
lock=open('/var/log/toddy/build/build.lock','a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
assert not list(Path('/var/log/toddy/build').glob('*.running.json'))
receipt=Path('/var/log/toddy/phase2')/(restore_name+'.json')
assert not receipt.exists(),'Inspect real restore receipt/mounts; never replay'
original=Path('/var/log/toddy/phase2')/('settings-scratch-custody-'+str(generation)+'.json')
assert hashlib.sha256(original.read_bytes()).hexdigest()==receipt_sha
saved=json.loads(original.read_text());assert saved['state']=='archive-stream-complete-source-unchanged'
root=Path('/run/toddy-samba-client-1');transport=Path('/run/toddy-settings-scratch-restore-1')
assert not root.exists() and not transport.exists()
assert shutil.disk_usage('/mnt/lfs').free>=16*1024**3
aliases=[r for r in saved['mounts'] if r['target']!=str(root)]
for row in aliases:
 target=Path(row['target']);assert target.is_relative_to('/mnt/lfs/sources') and not target.is_symlink()
 assert subprocess.run(['mountpoint','-q',str(target)]).returncode==32
 assert target.is_file() and target.stat().st_size==0 or target.is_dir() and not list(target.iterdir())
state={'state':'restore-intended','boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip(),'archive_sha256':archive_sha,'aliases':[]}
def save():
 part=receipt.with_suffix('.part');part.write_text(json.dumps(state,indent=2)+'\n');part.replace(receipt)
save()
root.mkdir(mode=0o700);transport.mkdir(mode=0o700)
subprocess.run(['mount','-t','tmpfs','-o','size=2G,mode=0700,nosuid,nodev','toddy-samba-client-1',str(root)],check=True)
subprocess.run(['mount','-t','tmpfs','-o','size=512M,mode=0700,nosuid,nodev,noexec','toddy-settings-scratch-restore-1',str(transport)],check=True)
archive=transport/'scratch.tar.gz';h=hashlib.sha256();total=0
with archive.open('xb') as f:
 os.fchmod(f.fileno(),0o600)
 while chunk:=sys.stdin.buffer.read(1024**2):
  total+=len(chunk);assert total<=archive_bytes
  h.update(chunk);f.write(chunk)
 f.flush();os.fsync(f.fileno())
assert total==archive_bytes and h.hexdigest()==archive_sha
state.update(state='archive-transferred',archive_bytes=total);save()
subprocess.run(['tar','--extract','--gzip','--file='+str(archive),'--directory='+str(root),'--numeric-owner','--same-owner','--acls','--xattrs','--sparse'],check=True)
sys.path.insert(0,'/opt/toddy-build/scripts/build/phase2')
from verify_settings_scratch_restore import verify
state['verification']=verify(root,saved,restore_times=True);state['state']='cache-verified';save()
for row in aliases:
 suffix=row['source'].removeprefix('toddy-samba-client-1[').removesuffix(']')
 assert suffix.startswith('/') and '..' not in Path(suffix).parts
 source=root/suffix.lstrip('/');target=Path(row['target'])
 assert source.exists() and not source.is_symlink()
 state['pending_alias']=str(target);save()
 subprocess.run(['mount','--bind',str(source),str(target)],check=True)
 options=row['options'].split(',');readonly='ro' in options
 flags=['remount','bind','ro' if readonly else 'rw','nosuid','nodev']+(['noexec'] if 'noexec' in options else [])
 subprocess.run(['mount','-o',','.join(flags),str(target)],check=True)
 actual=subprocess.check_output(['findmnt','-n','-o','OPTIONS','--mountpoint',str(target)],text=True).strip().split(',')
 assert all(flag in actual for flag in flags if flag not in ['remount','bind'])
 assert target.stat().st_ino==source.stat().st_ino
 state['aliases'].append({'target':str(target),'source':str(source),'readonly':readonly,'same_restored_inode':True});state.pop('pending_alias');save()
# Only the verified transfer copy is retired; the durable host archive is retained.
assert hashlib.sha256(archive.read_bytes()).hexdigest()==archive_sha
archive.unlink();subprocess.run(['umount',str(transport)],check=True);transport.rmdir()
state.update(state='complete',scope='Exact retained compiler/source/stage bytes, metadata and recorded aliases restored; no preparation, compiler, fixture or package transaction replay',scratch_available=shutil.disk_usage(root).free,target_available=shutil.disk_usage('/mnt/lfs').free)
assert state['scratch_available']>=128*1024**2 and state['target_available']>=16*1024**3
save();print(json.dumps(state))
'''


def main():
    global CONTEXT
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--receipt',default='native-owner-scratch-restored-1')
    parser.add_argument('--generation',type=int,choices=[1,2],default=1)
    args=parser.parse_args()
    CONTEXT=ROOT/'.local/phase2'/('settings-scratch-custody-'+str(args.generation))
    assert re.fullmatch(r'[a-z][a-z0-9-]{1,63}',args.receipt)
    receipt=json.loads((CONTEXT/'result.json').read_text())
    assert receipt['state']=='complete' and (CONTEXT/'restore-validation.exit').read_text().strip()=='0'
    archive=CONTEXT/'scratch.tar.gz'
    with archive.open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==receipt['archive_sha256']
    assert shutil.disk_usage(ROOT).free>=100*1024**3
    log=ROOT/'.local/phase2'/(args.receipt+'.log')
    assert not log.exists(),'Inspect actual guest receipt/aliases before any replay'
    code='generation='+repr(args.generation)+'\nrestore_name='+repr(args.receipt)+'\narchive_sha='+repr(receipt['archive_sha256'])+'\narchive_bytes='+repr(receipt['archive_bytes'])+'\nreceipt_sha='+repr(receipt['guest_receipt_sha256'])+'\n'+GUEST
    with archive.open('rb') as source,log.open('xb') as output:
        result=subprocess.run(phase2_vm.ssh_args()+['python3 -c '+shlex.quote(code)],stdin=source,stdout=output,stderr=subprocess.STDOUT)
    (log.with_suffix('.exit')).write_text(str(result.returncode)+'\n')
    assert result.returncode==0,'Preserve partial restore and inspect guest receipt, never replay'
    print(log.read_text())


if __name__=='__main__':main()
