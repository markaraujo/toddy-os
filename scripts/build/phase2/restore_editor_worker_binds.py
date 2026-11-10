"""Restore only existing private editor subtrees after their parent scratch mount."""
from pathlib import Path
import fcntl,hashlib,json,os,re,subprocess,sys

def main():
 name,=sys.argv[1:];assert re.fullmatch(r'[a-z][a-z0-9-]{1,80}',name) and os.geteuid()==0
 subprocess.run(['bash','-c','source /opt/toddy-build/scripts/build/target.sh; guard_target'],check=True)
 lock=open('/var/log/toddy/build/build.lock','a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 assert not list(Path('/var/log/toddy/build').glob('*.running.json'))
 log=Path('/var/log/toddy/phase2');receipt=log/(name+'.json');assert not receipt.exists() and not receipt.with_suffix('.part').exists(),'Inspect actual mounts/receipt; never replay'
 base=Path('/mnt/lfs/sources/phase2/work/doxygen-1');identity='ae4347fb-31fd-4193-a333-0a549e144231'
 assert subprocess.check_output(['findmnt','-n','-o','UUID','--mountpoint',str(base)],text=True).strip()==identity
 from native_scratch_staging import restore_workspace
 native_output=restore_workspace(base,log,name)
 from shared_source_inputs import restore_inputs
 input_aliases=restore_inputs(base,log,name)
 rows=[]
 components=['libspelling','editorconfig','gnome-text-editor']
 if (log/'gnome-bluetooth-shared-scratch-1.json').exists():components.append('gnome-bluetooth')
 if (log/'libmbim-shared-scratch-1.json').exists():components.append('libmbim')
 if (log/'libqmi-shared-scratch-1.json').exists():components.append('libqmi')
 if (log/'modemmanager-shared-scratch-1.json').exists():components.append('modemmanager')
 if (log/'libgtop-shared-scratch-1.json').exists():components.append('libgtop')
 for component in components:
  p=log/(component+'-shared-scratch-1.json');r=json.loads(p.read_text());assert r['state']=='mounted' and r['filesystem_uuid']==identity
  source=Path(r['source']);target=Path(r['target']);assert source==base/'toddy-editor-workers'/(component+'-1') and target==base.parent/(component+'-1')
  assert source.resolve()==source and source.stat().st_ino==r['source_inode'] and source.stat().st_uid==101
  assert target.resolve()==target and not list(target.iterdir()) and target.stat().st_uid==101
  assert subprocess.run(['mountpoint','-q',str(target)]).returncode==32
  rows.append({'source':str(source),'target':str(target),'inode':r['source_inode'],'preparation_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'state':'verified'})
 state={'state':'verified','scope':'Existing private subtree binds only; no image creation/format/resize/source or accepted build replay','boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip(),'filesystem_uuid':identity,'rows':rows,'source_input_aliases':input_aliases,'native_output':native_output}
 def save():
  part=receipt.with_suffix('.part');assert not part.exists()
  with part.open('x') as f:json.dump(state,f,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
  part.replace(receipt)
 save()
 for row in rows:
  row['state']='bind-intended';save();subprocess.run(['mount','--bind',row['source'],row['target']],check=True);subprocess.run(['mount','-o','remount,bind,nosuid,nodev',row['target']],check=True)
  assert Path(row['target']).stat().st_ino==row['inode'] and Path(row['target']).stat().st_dev==base.stat().st_dev
  row['state']='mounted';save()
 state['state']='complete';save();print(json.dumps(state))
if __name__=='__main__':main()
