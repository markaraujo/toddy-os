"""Preserve RAM compiler outputs with an actual unprivileged full restore proof."""
from pathlib import Path
import fcntl,hashlib,json,os,shutil,stat,subprocess,time
R=Path('/opt/toddy-build');T=Path('/mnt/lfs');W=T/'sources/phase2/work/git-1';L=Path('/var/log/toddy/phase2')
subprocess.run(['bash','-c','source /opt/toddy-build/scripts/build/target.sh; guard_target'],check=True)
lock=open('/var/log/toddy/build/build.lock','a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
assert not list(Path('/var/log/toddy/build').glob('*.running.json'))
r=json.loads(Path('/var/log/toddy/build/b02-git-install.success.json').read_text());assert r['recipe_exit']==r['postcheck_exit']==0
assert (L/'git-qualify-2.exit').read_text().strip()=='0'
receipt=L/'git-cache-custody-1.json';archive=Path('/var/cache/toddy/build/git-2.55.0-qualified-1.tar.gz');temporary=archive.with_suffix('.part');restore=Path('/run/toddy-git-restore-1')
assert not any(p.exists() or p.is_symlink() for p in [receipt,receipt.with_suffix('.part'),archive,temporary,restore])
def inventory(root):
 paths=[root]+sorted(root.rglob('*'));rows={};seen={};digests={};size=0
 for p in paths:
  name=str(p.relative_to(root));s=p.lstat();assert s.st_uid==s.st_gid==101,(name,s.st_uid,s.st_gid)
  row={'mode':s.st_mode,'uid':s.st_uid,'gid':s.st_gid,'mtime_ns':s.st_mtime_ns}
  if stat.S_ISREG(s.st_mode):
   identity=(s.st_dev,s.st_ino);first=seen.setdefault(identity,name);row['hardlink_class']=first
   if identity not in digests:
    with p.open('rb') as f:digests[identity]=hashlib.file_digest(f,'sha256').hexdigest()
    size+=s.st_size
   row.update(sha256=digests[identity],bytes=s.st_size)
  elif stat.S_ISLNK(s.st_mode):row['symlink']=os.readlink(p)
  else:assert stat.S_ISDIR(s.st_mode),name
  rows[name]=row
 return rows,size
before,size=inventory(W);assert shutil.disk_usage('/var/cache').free>size+512*1024**2
available=int(next(l.split()[1] for l in Path('/proc/meminfo').read_text().splitlines() if l.startswith('MemAvailable:')))*1024;assert available>size+512*1024**2
state={'state':'archive-intended','scope':'Qualified Git RAM outputs only; no install/runtime mutation. Actual full restore must pass before any builder cold stop.','source':str(W),'archive':str(archive),'entries':len(before),'unique_regular_bytes':size,'boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip()}
def save():
 p=receipt.with_suffix('.part');p.write_text(json.dumps(state,indent=2)+'\n');p.replace(receipt)
save();archive.parent.mkdir(parents=True,exist_ok=True)
subprocess.run(['tar','--format=pax','-czf',str(temporary),'-C',str(W),'.'],check=True);temporary.replace(archive)
with archive.open('rb') as f:state['archive_sha256']=hashlib.file_digest(f,'sha256').hexdigest()
state.update(state='restoring',archive_bytes=archive.stat().st_size);save()
restore.mkdir(mode=0o755);subprocess.run(['mount','-t','tmpfs','-o','size=1536m,nosuid,nodev','toddy-git-restore-1',str(restore)],check=True);os.chown(restore,101,101)
subprocess.run(['setpriv','--reuid=101','--regid=101','--clear-groups','--no-new-privs','tar','--no-same-owner','--same-permissions','-xzf',str(archive),'-C',str(restore)],check=True)
after,_=inventory(restore);assert after==before,'Preserve mismatch and inspect; never discard original RAM outputs'
state.update(state='complete',actual_restore_entries=len(after),actual_restore_bytes_modes_owners_timestamps_symlinks_hardlinks_equal=True);save()
subprocess.run(['umount',str(restore)],check=True);assert not list(restore.iterdir());restore.rmdir();print(json.dumps(state))
