#!/usr/bin/env python3
"""Give the companion a distinct work tree on existing Glycin scratch capacity."""
from pathlib import Path
import hashlib,json,shlex,subprocess,sys
import phase2_vm

def main():
 code='''from pathlib import Path
import fcntl,hashlib,json,os,subprocess
subprocess.run(['bash','-c','source /opt/toddy-build/scripts/build/target.sh; guard_target'],check=True)
lock=open('/var/log/toddy/build/build.lock','a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
assert not list(Path('/var/log/toddy/build').glob('*.running.json'))
p=Path('/var/log/toddy/phase2/glycin-gtk4-work-volume.json');assert not p.exists(),'Reconcile prior operation; never replay'
source=Path('/mnt/lfs/sources/phase2/inputs/glycin-2.1.5');assert source.is_dir()
prepared=json.loads((source/'toddy-prepared.json').read_text());assert prepared['sources'][0]['name'] in ('glycin','glycin-vendor')
rows=json.loads(Path('/opt/toddy-build/config/phase2/sources.lock.json').read_text())['components']
for row in prepared['sources']:assert row in rows
assert hashlib.sha256((source/'project/Cargo.lock').read_bytes()).hexdigest()==prepared['cargo_lock_sha256']
assert subprocess.check_output(['chroot','/mnt/lfs','pkg-config','--modversion','glycin-2'],text=True).strip()=='2.1.0'
assert subprocess.check_output(['chroot','/mnt/lfs','pkg-config','--modversion','gtk4'],text=True).strip()=='4.22.4'
parent=Path('/mnt/lfs/sources/phase2/work/glycin-1');volume=json.loads(Path('/var/log/toddy/phase2/glycin-build-volume.json').read_text())
uuid=subprocess.check_output(['findmnt','-n','-o','UUID','--mountpoint',str(parent)],text=True).strip();assert uuid==volume['filesystem_uuid']
free=os.statvfs(parent);assert free.f_bavail*free.f_frsize>=850*1024**2
fs=os.statvfs('/mnt/lfs');assert fs.f_bavail*fs.f_frsize>=16*1024**3
backing=parent/'gtk4-companion-work-1';work=Path('/mnt/lfs/sources/phase2/work/glycin-gtk4-1')
assert not backing.exists() and not work.exists()
state={'state':'preflight','source':str(source),'source_prepared_sha256':hashlib.sha256((source/'toddy-prepared.json').read_bytes()).hexdigest(),'backing':str(backing),'work':str(work),'parent_mount':str(parent),'filesystem_uuid':uuid,'free_scratch_bytes':free.f_bavail*free.f_frsize,'target_free_bytes':fs.f_bavail*fs.f_frsize,'minimum_scratch_reserve_bytes':128*1024**2,'recipe_sha256':RECIPE_SHA,'recovery':'Verify backing inode/UUID and absence of active writer before restoring only this bind; never recreate directories or replay prep. Existing Glycin production/test outputs are separate siblings, never build into them.'}
p.write_text(json.dumps(state,indent=2)+'\\n')
backing.mkdir(mode=0o755);os.chown(backing,101,101);state['backing_inode']=backing.stat().st_ino;state['state']='backing-created';p.write_text(json.dumps(state,indent=2)+'\\n')
work.mkdir(mode=0o755);state['mountpoint_inode']=work.stat().st_ino;state['state']='mountpoint-created';p.write_text(json.dumps(state,indent=2)+'\\n')
subprocess.run(['mount','--bind',str(backing),str(work)],check=True);assert work.stat().st_ino==state['backing_inode']
state['state']='mounted';p.write_text(json.dumps(state,indent=2)+'\\n');print(json.dumps(state))
'''
 recipe=Path('scripts/build/phase2/glycin_gtk4_build.py').read_bytes();code=code.replace('RECIPE_SHA',repr(hashlib.sha256(recipe).hexdigest()))
 out=Path('.local/phase2/glycin-gtk4-input.log');assert not out.exists()
 with out.open('x') as log:r=subprocess.run(phase2_vm.ssh_args()+['python3 -c '+shlex.quote(code)],stdout=log,stderr=subprocess.STDOUT,text=True)
 out.with_suffix('.exit').write_text(str(r.returncode)+'\n');raise SystemExit(r.returncode)
if __name__=='__main__':main()
