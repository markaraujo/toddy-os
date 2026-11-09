#!/usr/bin/env python3
"""Prepare one explicit Polkit subject-decoder correction, retaining original input."""
import hashlib,json,shlex,shutil,subprocess
from pathlib import Path
import phase2_vm
ROOT=phase2_vm.ROOT

def main():
    assert shutil.disk_usage(ROOT).free>=100*1024**3
    manifest=json.loads((ROOT/'config/phase2/polkit-patches.lock.json').read_text());patch=(ROOT/manifest['patch_file']).read_text();assert hashlib.sha256(patch.encode()).hexdigest()==manifest['patch_sha256']
    files={a:(ROOT/'scripts/build/phase2'/b).read_text() for a,b in [('toddy-build.sh','polkit-patched-library.sh'),('toddy-probe.c','polkit-strict-subject-probe.c')]}
    code=r'''from pathlib import Path
import fcntl,hashlib,json,os,shutil,subprocess,time
subprocess.run(['bash','-c','source /opt/toddy-build/scripts/build/target.sh; guard_target'],check=True)
lock=open('/var/log/toddy/build/build.lock','a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
assert not list(Path('/var/log/toddy/build').glob('*.running.json'))
'''+f'manifest={manifest!r}\npatch={patch!r}\nfiles={files!r}\n'+r'''
log=Path('/var/log/toddy/phase2');assert (log/'polkit-library-diagnosis-1.exit').read_text().strip()=='0'
original=Path('/mnt/lfs/sources/phase2/inputs/polkit-127');source=Path('/mnt/lfs/sources/phase2/inputs/polkit-127-typed-subject-1');work=Path('/mnt/lfs/sources/phase2/work/polkit-patched-library-1');receipt=log/'polkit-patched-input-1.json'
assert not source.exists() and not work.exists() and not receipt.exists(),'Reconcile prior input operation, never replay'
assert shutil.disk_usage('/mnt/lfs').free>=16*1024**3+32*1024**2
prepared=json.loads((original/'toddy-prepared.json').read_text());assert prepared['source_sha256']==manifest['source_sha256']
def inventory(root):
 result={}
 for p in root.rglob('*'):
  name=str(p.relative_to(root))
  if p.is_symlink():result[name]={'link':str(p.readlink())}
  elif p.is_file():
   with p.open('rb') as f:result[name]={'sha256':hashlib.file_digest(f,'sha256').hexdigest()}
 return result
before=inventory(original)
state={'state':'copying','source':str(source),'work':str(work),'boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip(),'pid':os.getpid(),'started_unix':time.time(),'patch_sha256':manifest['patch_sha256']}
def save():
 part=receipt.with_suffix('.part');assert not part.exists()
 with part.open('x') as f:json.dump(state,f,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
 part.replace(receipt)
save();shutil.copytree(original,source,symlinks=True);assert inventory(source)==before
path=source/manifest['source_file'];assert hashlib.sha256(path.read_bytes()).hexdigest()==manifest['before_sha256']
with (log/'polkit-patched-input-1-apply.log').open('x') as output:
 subprocess.run(['patch','--batch','--forward','--fuzz=0','-Np1'],input=patch,text=True,cwd=source,stdout=output,stderr=subprocess.STDOUT,check=True)
assert hashlib.sha256(path.read_bytes()).hexdigest()==manifest['after_sha256']
after=inventory(source);assert [n for n in before if before[n]!=after[n]]==[manifest['source_file']]
assert inventory(original)==before
for name,text in files.items():(source/name).write_text(text)
prepared.update(source_patches=[manifest],recipe_sha256=hashlib.sha256(files['toddy-build.sh'].encode()).hexdigest(),probe_sha256=hashlib.sha256(files['toddy-probe.c'].encode()).hexdigest())
(source/'toddy-prepared.json').write_text(json.dumps(prepared,indent=2)+'\n')
work.mkdir();os.chown(work,101,101)
state.update(state='complete',original_files_unchanged=len(before),modified_library_source_files=1);save();print(json.dumps(state))
'''
    compile(code,'polkit-patch-input','exec')
    subprocess.run(phase2_vm.ssh_args()+['python3 -c '+shlex.quote(code)],check=True)
if __name__=='__main__':main()
