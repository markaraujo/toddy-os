#!/usr/bin/env python3
"""Copy the authenticated small GtkSource input and apply only ADR0146's fix."""
import hashlib
import json
from pathlib import Path
import shlex
import subprocess
import phase2_vm

ROOT = phase2_vm.ROOT


def main():
    diagnostic = json.loads((ROOT / 'docs/evidence/B02-gtksourceview-duplicate-diagnosis.json').read_text())
    assert not diagnostic['changed_artifacts'] and diagnostic['commands'][-1]['exit'] == 0
    patch = (ROOT / 'patches/phase2/gtksourceview-5.20.0-duplicate-capture-1.patch').read_text()
    assert hashlib.sha256(patch.encode()).hexdigest() == diagnostic['patch_sha256']
    files = {'toddy-base-build.sh': (ROOT / 'scripts/build/phase2/gtksourceview-build.sh').read_text(),
             'toddy-probe.c': (ROOT / 'scripts/build/phase2/gtksourceview-probe.c').read_text(),
             'toddy-affected-tests.py': (ROOT / 'scripts/build/phase2/gtksourceview_patched_tests.py').read_text(),
             'toddy-build.sh': '#!/bin/bash\nset -euo pipefail\nbash /src/toddy-base-build.sh\npython3 -B /src/toddy-affected-tests.py\n'}
    code = r'''from pathlib import Path
import fcntl,hashlib,json,os,shutil,socket,subprocess,time
assert os.geteuid()==0 and socket.gethostname()=='toddy-builder'
subprocess.run(['bash','-c','source /opt/toddy-build/scripts/build/target.sh; guard_target'],check=True)
lock=open('/var/log/toddy/build/build.lock','a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
assert not list(Path('/var/log/toddy/build').glob('*.running.json'))
''' + f'files={files!r}\npatch={patch!r}\ndiagnostic={diagnostic!r}\n' + r'''
old=Path('/mnt/lfs/sources/phase2/inputs/gtksourceview-5.20.0')
source=old.with_name('gtksourceview-5.20.0-duplicate-1')
work=Path('/mnt/lfs/sources/phase2/work/gtksourceview-patched-1')
receipt=Path('/var/log/toddy/phase2/gtksourceview-patched-input-1.json')
assert old.resolve()==old and old.is_dir()
assert not source.exists() and not work.exists() and not receipt.exists(),'Reconcile actual operation before repeat'
assert shutil.disk_usage('/mnt/lfs').free>=16*1024**3+256*1024**2
original=json.loads((old/'toddy-prepared.json').read_text())
assert original['source_sha256']=='e38bcd23f52b86eadf0fe4d8bde698e3a8ca102322b8b4cf1a51ac294a448c1b'
def inventory(root):
 result={}
 for p in root.rglob('*'):
  name=str(p.relative_to(root))
  if p.is_symlink():result[name]={'link':os.readlink(p)}
  elif p.is_file():
   with p.open('rb') as f:result[name]={'sha256':hashlib.file_digest(f,'sha256').hexdigest()}
 return result
before=inventory(old)
state={'state':'copying','pid':os.getpid(),'boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip(),'proc_start_ticks':Path('/proc/self/stat').read_text().split()[21],'source':str(source),'work':str(work),'started_unix':time.time()}
def save():
 part=receipt.with_suffix('.part');assert not part.exists()
 with part.open('x') as f:json.dump(state,f,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
 part.replace(receipt)
save();shutil.copytree(old,source,symlinks=True,copy_function=shutil.copy2)
assert inventory(source)==before
p=source/'gtksourceview/implregex.c';assert hashlib.sha256(p.read_bytes()).hexdigest()==diagnostic['original_source_sha256']
state['state']='patching';save()
subprocess.run(['patch','--batch','--forward','--fuzz=0','-Np1'],input=patch,text=True,cwd=source,check=True)
assert hashlib.sha256(p.read_bytes()).hexdigest()==diagnostic['corrected_source_sha256']
after=inventory(source);assert [n for n in before if before[n]!=after[n]]==['gtksourceview/implregex.c']
assert inventory(old)==before,'Original source must remain unchanged'
for name,text in files.items():(source/name).write_text(text)
prepared={**original,'source_patches':[{'adr':'0146','path':'gtksourceview/implregex.c','before_sha256':diagnostic['original_source_sha256'],'after_sha256':diagnostic['corrected_source_sha256'],'patch_sha256':diagnostic['patch_sha256']}],'recipe_sha256':hashlib.sha256(files['toddy-build.sh'].encode()).hexdigest(),'probe_sha256':hashlib.sha256(files['toddy-probe.c'].encode()).hexdigest(),'original_input_files_unchanged':len(before),'capacity_budget_bytes':256*1024**2}
(source/'toddy-prepared.json').write_text(json.dumps(prepared,indent=2)+'\n')
work.mkdir();os.chown(work,101,101)
state.update(state='complete',prepared=prepared);save()
print(json.dumps({'state':'complete','source':str(source),'original_files_unchanged':len(before),'patched_source_files':1}))
'''
    compile(code, 'gtksource-patched-input', 'exec')
    subprocess.run(phase2_vm.ssh_args() + ['python3 -c ' + shlex.quote(code)], check=True)


if __name__ == '__main__':
    main()
