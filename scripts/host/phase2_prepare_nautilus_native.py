#!/usr/bin/env python3
"""Freeze compact, read-only native Nautilus inputs without copying target disks."""
import hashlib
import json
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import tarfile

import phase2_vm

ROOT=phase2_vm.ROOT
CONTEXT=ROOT/'.local/phase2/native-nautilus-inputs-1'
SELECTED=['validate-appdata','test-bookmarks','test-file','test-file-metadata',
          'test-file-operations-copy-files','test-file-operations-rename',
          'test-file-operations-trash-or-delete','test-filename-utilities',
          'test-nautilus-search-engine-simple','test-nautilus-directory-async',
          'test-file-operations-create','test-files-view']
GUEST=r'''
from pathlib import Path
import fcntl,hashlib,json,os,stat,subprocess,sys
subprocess.run(['bash','-c','source /opt/toddy-build/scripts/build/target.sh; guard_target'],check=True,stdout=sys.stderr)
lock=open('/var/log/toddy/build/build.lock','a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
assert not list(Path('/var/log/toddy/build').glob('*.running.json'))
log=Path('/var/log/toddy/phase2');receipt=log/'nautilus-native-cache-prepared-1.json';assert not receipt.exists()
assert (log/'nautilus-1.exit').read_text().strip()=='0'
base=Path('/run/toddy-samba-client-1');source=base/'nautilus-input-1/nautilus-50.2.2';work=base/'nautilus-work-1'
prepared=json.loads((source/'toddy-prepared.json').read_text());results=json.loads((work/'stage-results.json').read_text())
assert prepared['source_sha256']=='e1e285efddf42ed30dda5b29f7f8d242dab4bc1409a9054863b367bad4b34d5a'
assert results['compile_exit']==results['stage_exit']==0 and not results['original_tests_executed']
assert len(results['artifacts'])==277 and len(results['stage_sha256'])==154
inventory=json.loads((work/'original-test-inventory.json').read_text());selected=[next(r for r in inventory if r['name']==name) for name in chosen]
assert len(inventory)==24 and all(r['protocol']=='exitcode' and r['workdir'] is None for r in selected)
def digest(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def file_map(p):return {str(f.relative_to(p)):digest(f) for f in p.rglob('*') if f.is_file() and not f.is_symlink()}
def cache_manifest():
 rows={}
 for prefix in ['nautilus-input-1','nautilus-work-1']:
  paths=[base/prefix]+list((base/prefix).rglob('*'))
  for p in paths:
   s=p.lstat();r={'mode':s.st_mode,'uid':s.st_uid,'gid':s.st_gid,'mtime_ns':s.st_mtime_ns}
   if stat.S_ISREG(s.st_mode):r.update(type='file',bytes=s.st_size,sha256=digest(p),hardlink_identity=[s.st_dev,s.st_ino])
   elif stat.S_ISDIR(s.st_mode):r['type']='directory'
   elif stat.S_ISLNK(s.st_mode):r.update(type='symlink',target=os.readlink(p))
   else:raise AssertionError('Unexpected special native input')
   rows[str(p.relative_to(base))]=r
 return rows
assert file_map(work/'stage')==results['stage_sha256']
for name,sha in results['artifacts'].items():assert digest(work/'compile'/name)==sha
before=cache_manifest()
state={'state':'archiving','scope':'Exact compact Nautilus source/compiler/stage native-input transport only; no test/build/installation replay',
       'boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip(),'prepared':prepared,'cache_entries':before,
       'source_files':file_map(source),'compile_files':file_map(work/'compile'),'stage_files':results['stage_sha256'],
       'test_inventory':inventory,'selected_tests':selected,'not_selected':[r['name'] for r in inventory if r['name'] not in chosen],
       'compile_ELFs':results['artifacts'],'source_path':'/sources/phase2/inputs/nautilus-50.2.2','work_path':'/sources/phase2/work/nautilus-1'}
receipt.write_text(json.dumps(state,indent=2)+'\n')
r=subprocess.run(['tar','--create','--gzip','--file=-','--numeric-owner','--acls','--xattrs','--sparse','--one-file-system','-C',str(base),'nautilus-input-1','nautilus-work-1'])
assert r.returncode==0 and cache_manifest()==before
state['state']='archive-stream-complete-inputs-unchanged';receipt.write_text(json.dumps(state,indent=2)+'\n')
'''


def sha(path):
    with path.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()


def main():
    assert not CONTEXT.exists(),'Inspect existing raw image/receipt; never replay'
    custody=ROOT/'.local/phase2/settings-scratch-custody-2'
    proof=json.loads((custody/'result.json').read_text());assert proof['state']=='complete'
    assert (custody/'restore-validation.exit').read_text().strip()=='0'
    assert shutil.disk_usage(ROOT).free>=100*1024**3+1024**3
    CONTEXT.mkdir(mode=0o700);archive=CONTEXT/'cache.tar.gz'
    body='chosen='+repr(SELECTED)+'\n'+GUEST
    with archive.open('xb') as out,(CONTEXT/'prepare.log').open('xb') as log:
        os.fchmod(out.fileno(),0o600)
        r=subprocess.run(phase2_vm.ssh_args()+['python3 -'],input=body.encode(),stdout=out,stderr=log)
        out.flush();os.fsync(out.fileno())
    assert r.returncode==0,'Preserve incomplete transport and inspect actual guest receipt'
    raw_receipt=subprocess.check_output(phase2_vm.ssh_args()+['cat /var/log/toddy/phase2/nautilus-native-cache-prepared-1.json'])
    (CONTEXT/'producer.json').write_bytes(raw_receipt);descriptor=json.loads(raw_receipt)
    assert descriptor['state']=='archive-stream-complete-inputs-unchanged'
    expected=descriptor['cache_entries'];seen=set();links=[]
    with tarfile.open(archive,'r:gz') as tar:
        for member in tar:
            name=member.name.rstrip('/');assert name in expected and name not in seen,name
            assert not Path(name).is_absolute() and '..' not in Path(name).parts
            row=expected[name];seen.add(name)
            assert member.mode==row['mode']&0o7777 and member.uid==row['uid'] and member.gid==row['gid']
            if member.islnk():links.append((name,member.linkname))
            elif member.isfile():
                assert row['type']=='file' and member.size==row['bytes']
                assert hashlib.file_digest(tar.extractfile(member),'sha256').hexdigest()==row['sha256']
            elif member.isdir():assert row['type']=='directory'
            elif member.issym():assert row['type']=='symlink' and member.linkname==row['target']
            else:raise AssertionError('Unexpected archive type')
    assert seen==set(expected)
    for name,target in links:assert expected[name]['hardlink_identity']==expected[target]['hardlink_identity']
    image=CONTEXT/'cache.raw'
    with archive.open('rb') as source,image.open('xb') as output:
        os.fchmod(output.fileno(),0o600);shutil.copyfileobj(source,output)
        padding=(-output.tell())%512;output.write(bytes(padding));output.flush();os.fsync(output.fileno())
    transport={'archive_bytes':archive.stat().st_size,'archive_sha256':sha(archive),'raw_bytes':image.stat().st_size,'raw_sha256':sha(image),'device_serial':'TODDY-NAUTILUS-INPUT','readonly_required':True}
    descriptor.update(state='complete',transport=transport,focused_budget={'per_program_seconds':60,'whole_selected_seconds':300,'other_registered_programs':'Not run; retained owner-use backlog unless affected changes require them.'})
    data=(json.dumps(descriptor,indent=2)+'\n').encode()
    code="""from pathlib import Path
import fcntl,hashlib,json,os,sys
lock=open('/var/log/toddy/build/build.lock','a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
assert not list(Path('/var/log/toddy/build').glob('*.running.json'))
data=sys.stdin.buffer.read();record=json.loads(data);assert record['state']=='complete'
original=json.loads(Path('/var/log/toddy/phase2/nautilus-native-cache-prepared-1.json').read_text());assert original['state']=='archive-stream-complete-inputs-unchanged' and original['cache_entries']==record['cache_entries']
paths=[Path('/mnt/lfs/sources/phase2/native-fixtures/nautilus-1.json'),Path('/var/log/toddy/phase2/nautilus-native-fixture-1.json')]
assert all(not p.exists() for p in paths)
for p in paths:
 with p.open('xb') as f:os.fchmod(f.fileno(),0o600);f.write(data);f.flush();os.fsync(f.fileno())
print(hashlib.sha256(data).hexdigest())
"""
    r=subprocess.run(phase2_vm.ssh_args()+['python3 -c '+shlex.quote(code)],input=data,capture_output=True,check=True)
    fixture_sha=r.stdout.decode().strip();assert fixture_sha==hashlib.sha256(data).hexdigest()
    (CONTEXT/'fixture.json').write_bytes(data)
    result={'state':'complete','scope':'Verified compact read-only native input image, not a boot disk or test pass','fixture_sha256':fixture_sha,'verified_archive_entries':len(seen),'transport':transport,'selected_tests':SELECTED,'all_registered_tests':len(descriptor['test_inventory']),'custody_generation':2}
    (CONTEXT/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))


if __name__=='__main__':main()
