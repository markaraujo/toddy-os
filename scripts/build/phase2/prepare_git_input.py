"""Prepare one exact pinned Git source under the guarded guest target."""
from pathlib import Path
import fcntl,hashlib,json,os,subprocess,sys,tarfile
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from source_filter import source_filter,validate_source_members
R=Path('/opt/toddy-build');T=Path('/mnt/lfs');L=Path('/var/log/toddy/phase2')

def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main():
 assert os.getuid()==0 and len(sys.argv)==2
 name=sys.argv[1];assert name in ['git']
 subprocess.run(['bash','-c','source /opt/toddy-build/scripts/build/target.sh; guard_target'],check=True)
 lock=open('/var/log/toddy/build/build.lock','a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 assert not list(Path('/var/log/toddy/build').glob('*.running.json'))
 row=next(r for r in json.loads((R/'config/phase2/sources.lock.json').read_text())['components'] if r['name']==name)
 assert row['status']=='source_verified'
 recipe=R/'scripts/build/phase2'/(name+'-build.sh');assert recipe.is_file()
 source=T/'sources/phase2/inputs'/(name+'-'+row['version']);work=T/'sources/phase2/work'/(name+'-1');receipt=L/(name+'-source-prepared-1.json')
 assert not any(os.path.lexists(p) for p in [source,work,receipt,receipt.with_suffix('.part')]),'Inspect previous input/receipt before retry'
 assert os.statvfs(T).f_bavail*os.statvfs(T).f_frsize>=16*1024**3+128*1024**2
 archive=T/'sources'/row['filename'];temporary=archive.with_suffix(archive.suffix+'.git-part');assert not temporary.exists()
 r={'state':'prepare-intended','source':row,'source_path':str(source),'work_path':str(work),'boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip()}
 def save():
  p=receipt.with_suffix('.part');p.write_text(json.dumps(r,indent=2)+'\n');p.replace(receipt)
 save()
 if archive.exists():assert sha(archive)==row['sha256']
 else:
  h=hashlib.sha256();size=0
  with temporary.open('xb') as f:
   while chunk:=sys.stdin.buffer.read(1024**2):size+=len(chunk);assert size<=8*1024**2;h.update(chunk);f.write(chunk)
   f.flush();os.fsync(f.fileno())
  assert h.hexdigest()==row['sha256'];temporary.replace(archive)
 with tarfile.open(archive) as bundle:
  members=bundle.getmembers();assert all(Path(m.name).parts[0]==source.name for m in members)
  expanded=sum(m.size for m in members if m.isfile());assert expanded<=96*1024**2
  assert os.statvfs(T).f_bavail*os.statvfs(T).f_frsize>=16*1024**3+expanded+128*1024**2
  validate_source_members(archive.name,members);filtered=source_filter(archive.name)
  for member in members:filtered(member,source.parent)
  bundle.extractall(source.parent,filter=filtered)
 patches=[]
 if name=='fuse':
  p=source/'util/meson.build';before=sha(p);lines=p.read_text().splitlines(keepends=True)
  start=next(i for i,l in enumerate(lines) if l.startswith('udevrulesdir ='))
  p.write_text(''.join(lines[:start]+['#'+line for line in lines[start:]]))
  patches.append({'file':'util/meson.build','before_sha256':before,'after_sha256':sha(p),'reference':'Frozen BLFS13.1 postlfs/fuse.html: comment from /^udev/ to EOF, omitting unneeded init/udev/setuid install helper; explicit native privilege qualification separate.'})
 assert name=='git' and row['version']=='2.55.0'
 (source/'toddy-build.sh').write_bytes(recipe.read_bytes())
 (source/'toddy-build-result.py').write_bytes((R/'scripts/build/phase2/git_build_result.py').read_bytes())
 (source/'toddy-capacity-guard.py').write_bytes((R/'scripts/build/phase2/git_capacity_guard.py').read_bytes())
 prepared={'source_sha256':row['sha256'],'recipe_sha256':sha(recipe),'source_patches':patches,'scope':'Pinned source input only; isolated compile and native runtime/privilege tests remain required.'}

 (source/'toddy-prepared.json').write_text(json.dumps(prepared,indent=2)+'\n')
 work.mkdir(mode=0o755);os.chown(work,101,101)
 backing=Path('/run/toddy-git-build-1');assert not backing.exists()
 available=int(next(l.split()[1] for l in Path('/proc/meminfo').read_text().splitlines() if l.startswith('MemAvailable:')))*1024
 assert available>=2*1024**3,'Require bounded Git RAM workspace and compiler headroom'
 backing.mkdir(mode=0o755);subprocess.run(['mount','-t','tmpfs','-o','size=1536m,nosuid,nodev','toddy-git-build-1',str(backing)],check=True);os.chown(backing,101,101);backing.chmod(0o755)
 subprocess.run(['mount','--bind',str(backing),str(work)],check=True)
 subprocess.run(['mount','--bind',str(source),str(source)],check=True)
 subprocess.run(['mount','-o','remount,bind,ro,nosuid,nodev',str(source)],check=True)
 flags=set(subprocess.check_output(['findmnt','-n','-o','OPTIONS','--mountpoint',str(source)],text=True).strip().split(','));assert {'ro','nosuid','nodev'}<=flags
 r.update(state='prepared',expanded_bytes=expanded,recipe_sha256=prepared['recipe_sha256'],source_readonly=True,work_uid=work.stat().st_uid,workspace='bounded1536MiB RAM; archive qualified outputs before any cold reboot',capacity_guard_sha256=sha(source/'toddy-capacity-guard.py'));save();print(json.dumps(r))
if __name__=='__main__':main()
