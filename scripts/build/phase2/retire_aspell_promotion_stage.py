"""Retire only the installed, archive-identical Aspell promotion replica."""
from pathlib import Path
import fcntl,json,os,shutil,subprocess,sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from run_step import snapshot
from retire_llvm_stages import digest,verify_package_stage
from qualify_aspell import qualify

def main():
 assert os.geteuid()==0
 subprocess.run(['bash','-c','source /opt/toddy-build/scripts/build/target.sh; guard_target'],check=True)
 lock=open('/var/log/toddy/build/build.lock','a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 assert not list(Path('/var/log/toddy/build').glob('*.running.json'))
 assert not Path('/var/log/toddy/build/input-sync.running').exists()
 log=Path('/var/log/toddy/phase2');receipt=log/'aspell-promotion-stage-custody-1.json'
 assert not receipt.exists() and not receipt.with_suffix('.part').exists(),'Inspect actual state; never replay custody'
 verify=json.loads(Path('/var/log/toddy/build/b02-aspell-verify-2.success.json').read_text());assert verify['recipe_exit']==verify['postcheck_exit']==verify['changed_paths']==0
 assert json.loads((log/'aspell-info-metadata-1.json').read_text())['state']=='complete'
 record_path=Path('/var/log/toddy/packages/aspell_0.60.8.2-1+toddy1_amd64.json');record=json.loads(record_path.read_text())
 assert record['installed'] and digest(record_path)=='e845356375a7ad0d34ca7b68bc0b373db1d705ac7b947e84fc38b9fe3592600b'
 archive=Path('/var/cache/toddy/packages/aspell_0.60.8.2-1+toddy1_amd64.deb')
 expected='70368e76eaba8efe0c1195b7f23952eac5c5e49587ad1f9bc3df1df2e3735241'
 assert digest(archive)==record['archive_sha256']==expected
 assert subprocess.check_output(['chroot','/mnt/lfs','dpkg-query','-W','-f=${Status} ${Version}','aspell'],text=True)=='install ok installed 0.60.8.2-1+toddy1'
 root=Path('/opt/toddy-build');proof=qualify(root)
 stage=Path('/mnt/lfs/sources/stage/phase2-aspell')
 assert stage.resolve()==stage and stage.stat().st_ino==8074659 and {p.name for p in stage.iterdir()}=={'usr','DEBIAN'}
 verify_package_stage(stage,record['payload'])
 mounts=[Path(p) for p in subprocess.check_output(['findmnt','-rn','-o','TARGET'],text=True).splitlines()]
 assert not any(p==stage or p.is_relative_to(stage) for p in mounts)
 control={str(p.relative_to(stage)):digest(p) for p in (stage/'DEBIAN').rglob('*') if p.is_file()};assert control
 before=snapshot();space=os.statvfs('/mnt/lfs');free=space.f_bavail*space.f_frsize
 state={'state':'verified','scope':'Only closed Aspell native-promotion usr replica; installed payload/original source/compiler/workstage/dictionary/raw evidence/native archive/DEBIAN retained. No install/trim/rebuild replay.','stage':str(stage),'stage_inode':stage.stat().st_ino,'archive':str(archive),'archive_sha256':expected,'record_sha256':digest(record_path),'control':control,'qualified_compiler_ELFs':len(proof['artifacts']),'qualified_workstage_files':len(proof['stage_sha256']),'before_free_bytes':free}
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
