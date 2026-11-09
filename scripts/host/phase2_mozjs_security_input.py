#!/usr/bin/env python3
"""Prepare the explicit ADR0147 security candidate without mutating the baseline."""
import hashlib
import json
from pathlib import Path
import shlex
import shutil
import subprocess
import phase2_vm

ROOT=phase2_vm.ROOT


def main():
    assert shutil.disk_usage(ROOT).free>=100*1024**3, 'Preserve host reserve'
    frozen=json.loads((ROOT/'config/phase2/sources.lock.json').read_text())['components']
    rows=[next(r for r in frozen if r['name']==name) for name in ['mozjs-security-14017','mozjs-python314-patch']]
    raw_review=json.loads((ROOT/'.local/phase2/mozjs-14017-patch-review-1/result.json').read_text())
    review={'dry_run_exit':raw_review['old_patch_dry_run_exit'],'source_sha256':raw_review['archive_sha256'],'patch_sha256':raw_review['patch_sha256'],'paths':list(raw_review['paths'])};assert review['dry_run_exit']==0
    preflight=r'''import shutil,json
free=shutil.disk_usage('/mnt/lfs').free
assert free>=22*1024**3, 'Security candidate6GiB budget above16GiB reserve unavailable; no input mutation'
print(json.dumps({'target_free_bytes':free,'additional_budget_bytes':6*1024**3,'target_reserve_bytes':16*1024**3,'passed':True}))
'''
    subprocess.run(phase2_vm.ssh_args()+['python3 -c '+shlex.quote(preflight)],check=True)
    assert rows[0]['sha256']==review['source_sha256'] and rows[1]['sha256']==review['patch_sha256']
    for row in rows:
        path=ROOT/'.local/sources'/row['filename'];data=path.read_bytes();assert hashlib.sha256(data).hexdigest()==row['sha256']
        remote=r'''from pathlib import Path
import fcntl,hashlib,os,subprocess,sys
subprocess.run(['bash','-c','source /opt/toddy-build/scripts/build/target.sh; guard_target'],check=True)
l=open('/var/log/toddy/build/build.lock','a');fcntl.flock(l,fcntl.LOCK_EX|fcntl.LOCK_NB)
assert not list(Path('/var/log/toddy/build').glob('*.running.json'))
'''+f'row={row!r}\n'+r'''
p=Path('/mnt/lfs/sources')/row['filename'];part=p.with_name(p.name+'.part');assert not part.exists(),'Inspect interrupted source transfer before continuation'
data=sys.stdin.buffer.read();assert hashlib.sha256(data).hexdigest()==row['sha256']
if p.exists():
 with p.open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==row['sha256']
else:
 with part.open('xb') as f:f.write(data);f.flush();os.fsync(f.fileno())
 part.replace(p)
print(row['filename']+' verified')
'''
        compile(remote,'mozjs-transfer-preflight','exec')
        subprocess.run(phase2_vm.ssh_args()+['python3 -c '+shlex.quote(remote)],input=data,check=True)
    recipe=(ROOT/'scripts/build/phase2/mozjs-build.sh').read_text()
    assert recipe.count("assert '140.14' in version")==1
    recipe=recipe.replace('SpiderMonkey140.14','SpiderMonkey140.17 ADR0147 security candidate').replace("assert '140.14' in version","assert '140.17' in version")
    code=r'''from pathlib import Path
import fcntl,hashlib,json,os,shutil,socket,subprocess,time
assert os.geteuid()==0 and socket.gethostname()=='toddy-builder'
subprocess.run(['bash','-c','source /opt/toddy-build/scripts/build/target.sh; guard_target'],check=True)
l=open('/var/log/toddy/build/build.lock','a');fcntl.flock(l,fcntl.LOCK_EX|fcntl.LOCK_NB)
assert not list(Path('/var/log/toddy/build').glob('*.running.json'))
'''+f'rows={rows!r}\nrecipe={recipe!r}\nreview={review!r}\n'+r'''
source=Path('/mnt/lfs/sources/phase2/inputs/mozjs-tool-140.17.0');work=Path('/mnt/lfs/sources/phase2/work/mozjs-security-1');receipt=Path('/var/log/toddy/phase2/mozjs-security-input-1.json')
assert not source.exists() and not work.exists() and not receipt.exists(),'Reconcile existing operation before repeat'
status=subprocess.run(['chroot','/mnt/lfs','dpkg-query','-W','-f=${Status}','mozjs'],capture_output=True,text=True);assert status.returncode in (0,1) and status.stdout.strip()!='install ok installed'
assert shutil.disk_usage('/mnt/lfs').free>=22*1024**3-(Path('/mnt/lfs/sources')/rows[0]['filename']).stat().st_size
state={'state':'extracting','pid':os.getpid(),'boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip(),'proc_start_ticks':Path('/proc/self/stat').read_text().split()[21],'started_unix':time.time(),'source':str(source),'work':str(work),'source_sha256':rows[0]['sha256'],'patch_sha256':rows[1]['sha256']}
def save():
 part=receipt.with_suffix('.part');assert not part.exists()
 with part.open('x') as f:json.dump(state,f,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
 part.replace(receipt)
save();source.mkdir()
subprocess.run(['python3','/opt/toddy-build/scripts/build/source.py',rows[0]['filename']],cwd=source,check=True)
project=source/'firefox-140.17.0';assert project.is_dir() and not project.is_symlink();project.rename(source/'project');project=source/'project'
state['state']='patching';save()
before={name:hashlib.sha256((project/name).read_bytes()).hexdigest() for name in review['paths']}
patch=Path('/mnt/lfs/sources')/rows[1]['filename'];assert hashlib.sha256(patch.read_bytes()).hexdigest()==rows[1]['sha256']
subprocess.run(['patch','--batch','--forward','--fuzz=0','-Np1','-i',str(patch)],cwd=project,check=True)
after={name:hashlib.sha256((project/name).read_bytes()).hexdigest() for name in review['paths']};assert all(before[n]!=after[n] for n in before)
(source/'toddy-build.sh').write_text(recipe)
prepared={'scope':'Immutable Mozilla140.17 explicit security candidate source and exact required Python3.14 patch only; no compiler/runtime acceptance','sources':rows,'source_patches':[{'path':n,'before_sha256':before[n],'after_sha256':after[n],'patch_sha256':rows[1]['sha256']} for n in before],'adr':'0147','recipe_sha256':hashlib.sha256(recipe.encode()).hexdigest(),'host_patch_dry_run_exit':0,'free_bytes_before_build':shutil.disk_usage('/mnt/lfs').free}
(source/'toddy-prepared.json').write_text(json.dumps(prepared,indent=2)+'\n')
work.mkdir();os.chown(work,101,101);state.update(state='complete',prepared=prepared);save();print(json.dumps({'state':'complete','source':str(source),'patch_paths':len(before),'recipe_sha256':prepared['recipe_sha256']}))
'''
    compile(code,'mozjs-input-preflight','exec')
    prefix=ROOT/'.local/phase2/mozjs-security-input-1'
    with prefix.with_suffix('.log').open('xb') as log:r=subprocess.run(phase2_vm.ssh_args()+['python3 -c '+shlex.quote(code)],stdout=log,stderr=subprocess.STDOUT)
    prefix.with_suffix('.exit').write_text(str(r.returncode)+'\n');raise SystemExit(r.returncode)

if __name__=='__main__':main()
