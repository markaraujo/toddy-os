"""Retire eight archive-identical GTK promotion copies after actual restore checks."""
from pathlib import Path
import fcntl,hashlib,json,os,shutil,subprocess,sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from run_step import snapshot
from retire_llvm_stages import digest,verify_package_stage
T=Path('/mnt/lfs');L=Path('/var/log/toddy/phase2')
SELECTED=[('phase2-gtk',1),('phase2-gtk-desktop-schemas',2),('phase2-gtk-gtk3-schemas',3),('phase2-gtk-mutter-schemas',4),('phase2-gtk-session-schema-union',5),('phase2-gtk-ibus-schema-union',6),('phase2-gtk-gweather-schema-union',7),('phase2-gtk-desktop-schema-union',8)]
def free():
 s=os.statvfs(T);return s.f_bavail*s.f_frsize
def control_tree(path):
 rows={}
 for p in path.rglob('*'):
  st=p.lstat();r={'mode':st.st_mode,'uid':st.st_uid,'gid':st.st_gid}
  if p.is_file() and not p.is_symlink():r['sha256']=digest(p)
  else:assert p.is_dir() and not p.is_symlink()
  rows[str(p.relative_to(path))]=r
 return rows
def main():
 assert os.geteuid()==0
 subprocess.run(['bash','-c','source /opt/toddy-build/scripts/build/target.sh; guard_target'],check=True)
 lock=open('/var/log/toddy/build/build.lock','a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 assert not list(Path('/var/log/toddy/build').glob('*.running.json'))
 receipt=L/'gtk-schema-promotion-custody-1.json';restore=T/'sources/stage/gtk-schema-archive-restore-1'
 assert not receipt.exists() and not receipt.with_suffix('.part').exists() and not restore.exists(),'Reconcile prior operation; never replay uncertain retirement'
 assert subprocess.check_output(['chroot',str(T),'dpkg-query','-W','-f=${Status} ${Version}','gtk'],text=True)=='install ok installed 4.22.4-1+toddy8'
 rows=[];mounts=[Path(s) for s in subprocess.check_output(['findmnt','-rn','-o','TARGET'],text=True).splitlines()]
 for name,revision in SELECTED:
  stage=T/'sources/stage'/name;assert stage.resolve()==stage and stage.is_dir() and not stage.is_symlink() and not (stage/'.toddy-retired.json').exists()
  assert not any(m==stage or m.is_relative_to(stage) for m in mounts)
  version='4.22.4-1+toddy'+str(revision);record_path=Path('/var/log/toddy/packages','gtk_'+version+'_amd64.json');record=json.loads(record_path.read_text());assert record['installed'] and record['name']=='gtk' and record['version']==version
  archive=Path('/var/cache/toddy/packages',record_path.stem+'.deb');assert archive.is_file() and not archive.is_symlink() and digest(archive)==record['archive_sha256']
  verify_package_stage(stage,record['payload'])
  assert subprocess.check_output(['dpkg-deb','-f',str(archive),'Package','Version'],text=True).splitlines()==['Package: gtk','Version: '+version]
  rows.append({'stage':str(stage),'inode':stage.stat().st_ino,'version':version,'record':str(record_path),'record_sha256':digest(record_path),'archive':str(archive),'archive_sha256':record['archive_sha256'],'payload_entries':len(record['payload']),'control':control_tree(stage/'DEBIAN'),'state':'stage-and-archive-verified'})
 before=snapshot();state={'scope':'Eight exact GTK4 promotion replicas only; actual per-archive restore/data/control verification before retirement. Installed GTK/source/original compiler stages/tests/native archives/records retained. No old custody replay, trim or physical operation.','state':'verifying-restores','stages':rows,'before_free_bytes':free(),'producer_sha256':digest(Path(__file__))}
 def save():
  part=receipt.with_suffix('.part');assert not part.exists()
  with part.open('x') as f:json.dump(state,f,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
  part.replace(receipt)
 save();restore.mkdir()
 for row in rows:
  record=json.loads(Path(row['record']).read_text());size=sum((Path(row['stage'])/n.lstrip('/')).stat().st_size for n,r in record['payload'].items() if 'sha256' in r)
  assert free()>16*1024**3+size+32*1024**2
  out=restore/row['version'];assert not out.exists();row['state']='restoring';save()
  subprocess.run(['dpkg-deb','-x',row['archive'],str(out)],check=True)
  subprocess.run(['dpkg-deb','-e',row['archive'],str(out/'DEBIAN')],check=True)
  verify_package_stage(out,record['payload']);assert control_tree(out/'DEBIAN')==row['control']
  row['actual_restored_payload_entries']=len(record['payload']);row['actual_restored_control_verified']=True;row['state']='restore-verified';save()
  shutil.rmtree(out);assert not out.exists();print(json.dumps({'version':row['version'],'actual_restore_verified':True}),flush=True)
 restore.rmdir();assert all(r['state']=='restore-verified' for r in rows)
 state['state']='retiring';save()
 for row in rows:
  stage=Path(row['stage']);assert stage.stat().st_ino==row['inode'] and digest(Path(row['archive']))==row['archive_sha256'] and digest(Path(row['record']))==row['record_sha256']
  record=json.loads(Path(row['record']).read_text());verify_package_stage(stage,record['payload']);assert control_tree(stage/'DEBIAN')==row['control']
  row['state']='retiring';save()
  for name in ['usr','etc']:
   child=stage/name
   if child.exists():assert child.is_dir() and not child.is_symlink();shutil.rmtree(child)
  (stage/'.toddy-retired.json').write_text(json.dumps({'receipt':str(receipt),'archive':row['archive'],'archive_sha256':row['archive_sha256'],'recovery':'Verify/extract retained archive to NEW stage; never reinstall/replay retirement'},indent=2)+'\n')
  assert not (stage/'usr').exists();row['state']='retired';save()
 assert snapshot()==before,'Installed root changed; preserve custody and diagnose'
 state.update(state='complete',installed_root_changed_paths=0,after_free_bytes=free(),recovery='Verify retained archive/record SHA, extract to NEW stage as actually qualified here. Do not reinstall GTK or replay any retirement. Original compile stages/source/test evidence retained.')
 state['reclaimed_bytes']=state['after_free_bytes']-state['before_free_bytes'];save();print(json.dumps({'state':state['state'],'reclaimed_bytes':state['reclaimed_bytes'],'installed_root_changed_paths':0}),flush=True)
if __name__=='__main__':main()
