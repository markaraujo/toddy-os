#!/usr/bin/env python3
"""Prepare a new full build, preserving original and corrected library diagnoses."""
import hashlib,json,shlex,subprocess
from pathlib import Path
import phase2_vm

def main():
    root=phase2_vm.ROOT
    recipe=(root/'scripts/build/phase2/polkit-full-build.sh').read_text()
    patch=json.loads((root/'config/phase2/polkit-patches.lock.json').read_text())
    code='''from pathlib import Path
import fcntl,hashlib,json,os,shutil,subprocess,time
subprocess.run(['bash','-c','source /opt/toddy-build/scripts/build/target.sh; guard_target'],check=True)
lock=open('/var/log/toddy/build/build.lock','a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
assert not list(Path('/var/log/toddy/build').glob('*.running.json'))
'''+f'recipe={recipe!r}\npatch={patch!r}\n'+'''
log=Path('/var/log/toddy/phase2');assert (log/'polkit-patched-library-1.exit').read_text().strip()=='0'
old=Path('/mnt/lfs/sources/phase2/inputs/polkit-127-typed-subject-1')
source=Path('/mnt/lfs/sources/phase2/inputs/polkit-127-full-1');work=Path('/mnt/lfs/sources/phase2/work/polkit-full-1');receipt=log/'polkit-full-input-1.json'
assert not source.exists() and not work.exists() and not receipt.exists(),'Reconcile prior input, no replay'
assert hashlib.sha256((old/patch['source_file']).read_bytes()).hexdigest()==patch['after_sha256']
assert shutil.disk_usage('/mnt/lfs').free>=16*1024**3+64*1024**2
state={'state':'copying','source':str(source),'work':str(work),'boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip(),'pid':os.getpid(),'started_unix':time.time()}
def save():
 part=receipt.with_suffix('.part');assert not part.exists()
 with part.open('x') as f:json.dump(state,f,indent=2);f.write('\\n');f.flush();os.fsync(f.fileno())
 part.replace(receipt)
def inventory(base):
 return {str(p.relative_to(base)):(('link',str(p.readlink())) if p.is_symlink() else ('sha256',hashlib.sha256(p.read_bytes()).hexdigest())) for p in base.rglob('*') if p.is_symlink() or p.is_file()}
before=inventory(old);save();shutil.copytree(old,source,symlinks=True);assert inventory(source)==before
(source/'toddy-build.sh').write_text(recipe)
prepared=json.loads((source/'toddy-prepared.json').read_text());prepared.update(recipe_sha256=hashlib.sha256(recipe.encode()).hexdigest(),native_original_suite_required=True)
(source/'toddy-prepared.json').write_text(json.dumps(prepared,indent=2)+'\\n')
assert inventory(old)==before
work.mkdir();os.chown(work,101,101)
state.update(state='complete',original_files_unchanged=len(before),recipe_sha256=hashlib.sha256(recipe.encode()).hexdigest());save();print(json.dumps(state))
'''
    compile(code,'polkit-full-input','exec')
    subprocess.run(phase2_vm.ssh_args()+['python3 -c '+shlex.quote(code)],check=True)
if __name__=='__main__':main()
