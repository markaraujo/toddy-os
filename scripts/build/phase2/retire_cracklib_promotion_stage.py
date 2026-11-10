"""Retire only the installed, archive-identical Cracklib promotion replica."""
from pathlib import Path
import fcntl,json,os,shutil,subprocess,sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from run_step import snapshot
from retire_llvm_stages import digest,verify_package_stage
from qualify_cracklib import qualify

def main():
 assert os.geteuid()==0
 subprocess.run(['bash','-c','source /opt/toddy-build/scripts/build/target.sh; guard_target'],check=True)
 lock=open('/var/log/toddy/build/build.lock','a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 assert not list(Path('/var/log/toddy/build').glob('*.running.json'))
 assert not Path('/var/log/toddy/build/input-sync.running').exists()
 log=Path('/var/log/toddy/phase2');receipt=log/'cracklib-promotion-stage-custody-1.json'
 assert not receipt.exists() and not receipt.with_suffix('.part').exists(),'Inspect actual state; never replay custody'
 verify=json.loads(Path('/var/log/toddy/build/b02-cracklib-install.success.json').read_text());assert verify['recipe_exit']==verify['postcheck_exit']==0
 record_path=Path('/var/log/toddy/packages/cracklib_2.10.3-1+toddy1_amd64.json');record=json.loads(record_path.read_text())
 assert record['installed'] and digest(record_path)=='5b9768845431309ddbb968ca2cb3ddca8d1cbb147e22740c04e1774131d449c2'
 archive=Path('/var/cache/toddy/packages/cracklib_2.10.3-1+toddy1_amd64.deb')
 expected='aed1f98dff197653bd94860bb84cd53345de16a957035d3f7954a3fb08028613'
 assert digest(archive)==record['archive_sha256']==expected
 assert subprocess.check_output(['chroot','/mnt/lfs','dpkg-query','-W','-f=${Status} ${Version}','cracklib'],text=True)=='install ok installed 2.10.3-1+toddy1'
 root=Path('/opt/toddy-build');proof=qualify(root)
 stage=Path('/mnt/lfs/sources/stage/phase2-cracklib')
 assert stage.resolve()==stage and stage.stat().st_ino==9249083 and {p.name for p in stage.iterdir()}=={'usr','DEBIAN'}
 verify_package_stage(stage,record['payload'])
 for relative,row in record['payload'].items():
  installed=Path('/mnt/lfs')/relative.lstrip('/')
  if 'sha256' in row:assert digest(installed)==row['sha256']
  if 'symlink' in row:assert os.readlink(installed)==row['symlink']
 mounts=[Path(p) for p in subprocess.check_output(['findmnt','-rn','-o','TARGET'],text=True).splitlines()]
 assert not any(p==stage or p.is_relative_to(stage) for p in mounts)
 control={str(p.relative_to(stage)):digest(p) for p in (stage/'DEBIAN').rglob('*') if p.is_file()};assert control
 before=snapshot();space=os.statvfs('/mnt/lfs');free=space.f_bavail*space.f_frsize
 state={'state':'verified','scope':'Only closed Cracklib native-promotion usr replica; installed payload/original source/compiler/workstage/dictionary/raw evidence/native archive/DEBIAN retained. No install/trim/rebuild replay.','stage':str(stage),'stage_inode':stage.stat().st_ino,'archive':str(archive),'archive_sha256':expected,'record_sha256':digest(record_path),'control':control,'qualified_compiler_ELFs':len(proof['artifacts']),'qualified_workstage_files':len(proof['stage_sha256']),'before_free_bytes':free}
 def save():
  part=receipt.with_suffix('.part');assert not part.exists()
  with part.open('x') as f:json.dump(state,f,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
  part.replace(receipt)
 save();assert stage.stat().st_ino==state['stage_inode'];state['state']='retiring';save()
 shutil.rmtree(stage/'usr')
 (stage/'.toddy-retired.json').write_text(json.dumps({'receipt':str(receipt),'archive':str(archive),'archive_sha256':expected},indent=2)+'\n')
 assert not (stage/'usr').exists() and control=={str(p.relative_to(stage)):digest(p) for p in (stage/'DEBIAN').rglob('*') if p.is_file()}
 assert snapshot()==before,'Installed root changed; preserve evidence and diagnose'
 assert qualify(root)==proof and digest(archive)==expected
 space=os.statvfs('/mnt/lfs');state.update(state='complete',installed_root_changed_paths=0,after_free_bytes=space.f_bavail*space.f_frsize,recovery='Verify retained native archive/record hashes and extract to a NEW stage if needed. Never reinstall, replay custody, or retire the original compiler/workstage.');state['reclaimed_bytes']=state['after_free_bytes']-free;save()
 print(json.dumps({k:state[k] for k in ['state','reclaimed_bytes','installed_root_changed_paths','after_free_bytes']}))
if __name__=='__main__':main()
