#!/usr/bin/env python3
"""Prepare immutable Rust source/official seed inputs; never build or install."""
import hashlib
import json
from pathlib import Path
import shlex
import subprocess
import phase2_vm

ROOT=phase2_vm.ROOT
if __name__=='__main__':
    prefix=ROOT/'.local/phase2/rustc-input'
    assert not prefix.with_suffix('.log').exists() and not prefix.with_suffix('.exit').exists(),'Reconcile previous input preparation first'
    space=__import__('os').statvfs(ROOT)
    assert space.f_bavail*space.f_frsize>=112*1024**3,'Preserve100GiB host reserve and compiler growth headroom'
    rows=json.loads((ROOT/'config/phase2/sources.lock.json').read_text())['components']
    names=['rustc','rustc-stage0','rust-std-stage0','cargo-stage0']
    selected=[next(r for r in rows if r['name']==name) for name in names]
    assert selected[0]['version']=='1.97.1' and all(r['version']=='1.96.0' for r in selected[1:])
    recipe=(ROOT/'scripts/build/phase2/rustc-build.sh').read_text()
    config=(ROOT/'config/phase2/rust-bootstrap.toml').read_text()
    prepare='''from pathlib import Path
import fcntl,hashlib,json,os,subprocess
subprocess.run(['bash','-c','source /opt/toddy-build/scripts/build/target.sh; guard_target'],check=True)
lock=open('/var/log/toddy/build/build.lock','a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
assert not list(Path('/var/log/toddy/build').glob('*.running.json'))
'''+f'rows={selected!r}\nrecipe={recipe!r}\nconfig={config!r}\n'+'''
base=Path('/mnt/lfs/sources');root=base/'phase2/inputs/rust-toolchain-1.97.1';work=base/'phase2/work/rustc-1'
assert not root.exists() and not work.exists(),'Reconcile existing Rust source/work; no replay'
s=os.statvfs(base);assert s.f_bavail*s.f_frsize>=24*1024**3
root.mkdir();(root/'bootstrap').mkdir()
for row in rows:
 destination=root if row['name']=='rustc' else root/'bootstrap'
 subprocess.run(['python3','/opt/toddy-build/scripts/build/source.py',row['filename']],cwd=destination,check=True)
(root/'toddy-build.sh').write_text(recipe);(root/'bootstrap.toml').write_text(config)
receipt={'scope':'Immutable Rust source plus official build-only seeds; no compiler execution/install',
         'sources':rows,'recipe_sha256':hashlib.sha256(recipe.encode()).hexdigest(),
         'config_sha256':hashlib.sha256(config.encode()).hexdigest()}
(root/'toddy-prepared.json').write_text(json.dumps(receipt,indent=2)+chr(10))
work.mkdir();os.chown(work,101,101)
s=os.statvfs(base);receipt['free_bytes_after_prepare']=s.f_bavail*s.f_frsize
print(json.dumps(receipt),flush=True)
'''
    compile(prepare,'<native-rust-input>','exec')
    for row in selected:
        source=ROOT/'.local/sources'/row['filename']
        with source.open('rb') as stream:assert hashlib.file_digest(stream,'sha256').hexdigest()==row['sha256']
        transfer='''from pathlib import Path
import fcntl,hashlib,os,subprocess,sys
subprocess.run(['bash','-c','source /opt/toddy-build/scripts/build/target.sh; guard_target'],check=True)
lock=open('/var/log/toddy/build/build.lock','a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
assert not list(Path('/var/log/toddy/build').glob('*.running.json'))
assert not Path('/mnt/lfs/sources/phase2/inputs/rust-toolchain-1.97.1').exists() and not Path('/mnt/lfs/sources/phase2/work/rustc-1').exists(),'Reconcile prior Rust inputs/work before transfers'
'''+f'row={row!r}\n'+'''
target=Path('/mnt/lfs/sources')/row['filename'];part=target.with_name(target.name+'.part')
assert not part.exists(),'Reconcile partial source transfer first'
if target.exists():
 with target.open('rb') as stream:assert hashlib.file_digest(stream,'sha256').hexdigest()==row['sha256']
 assert hashlib.file_digest(sys.stdin.buffer,'sha256').hexdigest()==row['sha256']
else:
 digest=hashlib.sha256()
 with part.open('xb') as out:
  while chunk:=sys.stdin.buffer.read(1024*1024):out.write(chunk);digest.update(chunk)
  out.flush();os.fsync(out.fileno())
 assert digest.hexdigest()==row['sha256'];part.rename(target)
'''
        compile(transfer,'<native-rust-transfer>','exec')
        with source.open('rb') as stream:subprocess.run(phase2_vm.ssh_args()+['python3 -c '+shlex.quote(transfer)],stdin=stream,check=True)
    with prefix.with_suffix('.log').open('xb') as log:
        result=subprocess.run(phase2_vm.ssh_args()+['python3 -c '+shlex.quote(prepare)],stdout=log,stderr=subprocess.STDOUT)
    prefix.with_suffix('.exit').write_text(str(result.returncode)+'\n')
    raise SystemExit(result.returncode)
