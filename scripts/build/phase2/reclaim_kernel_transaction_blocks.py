"""Discard only newly free virtual target blocks with full retained-data checks."""
from pathlib import Path
import fcntl,gzip,hashlib,json,os,subprocess,sys,time
sys.path.insert(0,'/opt/toddy-build/scripts/build')
from run_step import snapshot
from kernel_cache_baseline import inventory,LOWER,WORK
from prepare_kernel_landlock_cow import metadata_same
L=Path('/var/log/toddy/phase2');RECEIPT=L/'kernel-transaction-discard-1.json'
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main():
 assert os.getuid()==0
 subprocess.run(['bash','-c','source /opt/toddy-build/scripts/build/target.sh; guard_target'],check=True)
 lock=open('/var/log/toddy/build/build.lock','a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 assert not list(Path('/var/log/toddy/build').glob('*.running.json'))
 for step in ['b02-linux-kernel-landlock-install','b02-boot-config-landlock-install']:
  r=json.loads((Path('/var/log/toddy/build')/(step+'.success.json')).read_text());assert r['recipe_exit']==r['postcheck_exit']==0
 assert not RECEIPT.exists() and not RECEIPT.with_suffix('.part').exists(),'Inspect actual trim/checkpoint/result before any repeat'
 assert Path('/sys/class/block/vdb/serial').read_text().strip()=='TODDY-LFS-TARGET'
 assert subprocess.check_output(['findmnt','-n','-o','SOURCE','--mountpoint','/mnt/lfs'],text=True).strip()=='/dev/vdb4'
 assert int(Path('/sys/class/block/vdb/queue/discard_max_bytes').read_text())>0
 assert sha(WORK/'baseline.json')=='d0e66e8e3cc2260d35242a1dca634e72bfd6bcd3d63a5bd94bac591a173114bf'
 kernel=json.loads((WORK/'baseline.json').read_text());metadata_same(kernel['cache'])
 before_path=L/'kernel-transaction-before-full-1.json.gz';assert not before_path.exists();before=snapshot()
 with before_path.open('xb') as f:
  os.fchmod(f.fileno(),0o600)
  with gzip.GzipFile(fileobj=f,mode='wb',mtime=0) as zipped:zipped.write(json.dumps(before,sort_keys=True,separators=(',',':')).encode())
  f.flush();os.fsync(f.fileno())
 state={'state':'checkpointed','scope':'Only free-block discard on current designated virtual /dev/vdb4, no file deletion/format/physical operation','boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip(),'full_entries_before':len(before),'before_full_gzip_sha256':sha(before_path),'kernel_cache_baseline_sha256':sha(WORK/'baseline.json'),'kernel_entries_before':len(kernel['cache'])}
 def save():
  part=RECEIPT.with_suffix('.part');part.write_text(json.dumps(state,indent=2)+'\n');part.replace(RECEIPT)
 save();print('Checkpoint complete; original cache metadata unchanged',flush=True)
 state['state']='trim-intended';save()
 with (L/'kernel-transaction-discard-1.log').open('xb') as out:r=subprocess.run(['fstrim','--verbose','/mnt/lfs'],stdout=out,stderr=subprocess.STDOUT)
 (L/'kernel-transaction-discard-1.exit').write_text(str(r.returncode)+'\n');state.update(state='trim-returned',trim_exit=r.returncode);save();assert r.returncode==0
 after=snapshot();changes=[p for p in before.keys()|after.keys() if before.get(p)!=after.get(p)];state.update(full_entries_after=len(after),changed_paths=changes,state='os-checked');save();assert not changes,'Preserve changed paths; do not replay trim'
 print('Full installed OS before/after identical; checking original kernel cache',flush=True)
 retained=inventory(LOWER);assert retained==kernel['cache'],'Preserve kernel differences; no trim replay'
 state.update(state='complete',kernel_entries_after=len(retained),kernel_cache_bytes_unchanged=True,installed_os_bytes_and_metadata_unchanged=True);save();print(json.dumps(state))
if __name__=='__main__':main()
