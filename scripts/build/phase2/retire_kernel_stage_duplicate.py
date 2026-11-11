"""Restore/compare the qualified archive before retiring only duplicate staging."""
from pathlib import Path
import fcntl,hashlib,json,os,shutil,subprocess
T=Path('/mnt/lfs');W=T/'sources/phase2/work/kernel-landlock-1';L=Path('/var/log/toddy/phase2')

def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main():
 assert os.getuid()==0
 subprocess.run(['bash','-c','source /opt/toddy-build/scripts/build/target.sh; guard_target'],check=True)
 lock=open('/var/log/toddy/build/build.lock','a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 assert not list(Path('/var/log/toddy/build').glob('*.running.json'))
 receipt=L/'kernel-stage-custody-for-fuse-1.json';temp=Path('/run/toddy-kernel-stage-custody-1');stage=W/'stage'
 assert not receipt.exists() and not receipt.with_suffix('.part').exists() and not temp.exists(),'Inspect actual prior custody; never replay uncertain retirement'
 assert not stage.is_symlink() and stage.is_dir() and list(stage.iterdir())
 assert subprocess.run(['mountpoint','-q',str(stage)]).returncode==32
 assert subprocess.check_output(['findmnt','-n','-o','UUID','--mountpoint',str(W)],text=True).strip()=='c6c4176d-faed-4ee3-9ae0-94914a0af666'
 r=json.loads(Path('/var/log/toddy/packages/linux-kernel_7.1.8-1+toddy1_amd64.json').read_text());assert r['installed']
 archive=Path('/var/cache/toddy/packages/linux-kernel_7.1.8-1+toddy1_amd64.deb');assert sha(archive)==r['archive_sha256']
 def verify(root,controls=False):
  actual={'/'+str(p.relative_to(root)) for p in root.rglob('*') if not controls or p.relative_to(root).parts[0]!='DEBIAN'}
  assert actual==set(r['payload']),list(actual.symmetric_difference(r['payload']))[:10]
  for name,row in r['payload'].items():
   p=root/name.lstrip('/');assert p.lstat().st_mode==row['mode'],name
   if 'sha256' in row:assert sha(p)==row['sha256'],name
   elif 'symlink' in row:assert p.is_symlink() and os.readlink(p)==row['symlink'],name
 verify(stage,True)
 row={'state':'restore-intended','archive_sha256':r['archive_sha256'],'archive_bytes':archive.stat().st_size,'payload_entries':len(r['payload']),'free_before':shutil.disk_usage(W).free,'scope':'Only completed duplicate native kernel stage; original source/COW compiler cache/installed payload and qualified package archive preserved.'}
 def save():
  part=receipt.with_suffix('.part');part.write_text(json.dumps(row,indent=2)+'\n');part.replace(receipt)
 save();temp.mkdir(mode=0o700)
 subprocess.run(['mount','-t','tmpfs','-o','size=192M,mode=0700,nosuid,nodev,noexec','toddy-kernel-stage-custody',str(temp)],check=True)
 subprocess.run(['dpkg-deb','--extract',str(archive),str(temp)],check=True)
 verify(temp)
 # Installed package has extra unrelated paths; compare only its owned payload.
 for name,payload in r['payload'].items():
  p=T/name.lstrip('/')
  if 'sha256' in payload:assert sha(p)==payload['sha256'],name
  elif 'symlink' in payload:assert os.readlink(p)==payload['symlink'],name
 row.update(state='restore-verified-retirement-intended',actual_archive_restore_verified=True,stage_exact_owned_payload=True,installed_payload_unchanged=True);save()
 for child in list(stage.iterdir()):
  if child.is_dir() and not child.is_symlink():shutil.rmtree(child)
  else:child.unlink()
 assert not list(stage.iterdir()) and sha(archive)==r['archive_sha256']
 subprocess.run(['umount',str(temp)],check=True);temp.rmdir()
 row.update(state='complete',free_after=shutil.disk_usage(W).free,stage_retired=True);assert row['free_after']>=300*1024**2;save();print(json.dumps(row))
if __name__=='__main__':main()
