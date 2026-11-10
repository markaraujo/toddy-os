"""Make one guarded private metadata-COW view of the preserved native kernel cache."""
from pathlib import Path
import fcntl,hashlib,json,os,stat,subprocess,time
from kernel_cache_baseline import LOWER,WORK
BASELINE_SHA='d0e66e8e3cc2260d35242a1dca634e72bfd6bcd3d63a5bd94bac591a173114bf'
INPUT=Path('/mnt/lfs/sources/phase2/inputs/linux-landlock-7.1.8')
RECEIPT=Path('/var/log/toddy/phase2/kernel-landlock-cow-1.json')

def save(row):
 part=RECEIPT.with_suffix('.part');assert not part.exists()
 with part.open('x') as f:f.write(json.dumps(row,indent=2)+'\n');f.flush();os.fsync(f.fileno())
 part.replace(RECEIPT)

def metadata_same(cache):
 actual={str(p.relative_to(LOWER)):p for p in [LOWER,*LOWER.rglob('*')]}
 assert set(actual)==set(cache)
 for key,row in cache.items():
  p=actual[key];s=p.lstat()
  assert {n:getattr(s,'st_'+n) for n in ['mode','uid','gid','size','mtime_ns','ino']}=={n:row['inode' if n=='ino' else n] for n in ['mode','uid','gid','size','mtime_ns','ino']},key
  if 'link' in row:assert os.readlink(p)==row['link']

def main():
 assert os.getuid()==0
 subprocess.run(['bash','-c','source /opt/toddy-build/scripts/build/target.sh; guard_target'],check=True)
 lock=open('/var/log/toddy/build/build.lock','a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 assert not list(Path('/var/log/toddy/build').glob('*.running.json'))
 assert not RECEIPT.exists() and not RECEIPT.with_suffix('.part').exists(),'Reconcile existing COW/mounts; never replay'
 assert not INPUT.exists() and not (WORK/'private-overlay').exists() and not (WORK/'merged').exists()
 assert subprocess.check_output(['findmnt','-n','-o','UUID','--mountpoint',str(WORK)],text=True).strip()=='c6c4176d-faed-4ee3-9ae0-94914a0af666'
 data=(WORK/'baseline.json').read_bytes();assert hashlib.sha256(data).hexdigest()==BASELINE_SHA
 baseline=json.loads(data);metadata_same(baseline['cache'])
 assert os.statvfs('/mnt/lfs').f_bavail*os.statvfs('/mnt/lfs').f_frsize>=16*1024**3
 assert os.statvfs(WORK).f_bavail*os.statvfs(WORK).f_frsize>512*1024**2
 row={'state':'preparation-intended','scope':'Only private scratch overlay/mount/ownership metadata, original cache must stay byte/metadata identical; not a kernel config/build/boot acceptance','baseline_sha256':BASELINE_SHA,'lower':str(LOWER),'work':str(WORK),'input':str(INPUT),'boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip()};save(row)
 private=WORK/'private-overlay';private.mkdir(mode=0o700)
 for name in ['lower','upper','work']:(private/name).mkdir()
 merged=WORK/'merged';merged.mkdir()
 subprocess.run(['mount','--bind',str(LOWER),str(private/'lower')],check=True)
 subprocess.run(['mount','-o','remount,bind,ro,nosuid,nodev',str(private/'lower')],check=True)
 subprocess.run(['mount','-t','overlay','overlay','-o',f'lowerdir={private}/lower,upperdir={private}/upper,workdir={private}/work,metacopy=on,index=off',str(merged)],check=True)
 changed=0
 for key,item in baseline['cache'].items():
  if stat.S_ISDIR(item['mode']) or key not in baseline['pristine_source']:
   os.chown(merged/key,101,101,follow_symlinks=False);changed+=1
 # Every promoted regular file must still be metadata-only, not copied data.
 regular=0;blocks=0
 for p in (private/'upper').rglob('*'):
  if p.is_file() and not p.is_symlink():
   assert p.stat().st_size==0 or 'trusted.overlay.metacopy' in os.listxattr(p),str(p)
   assert p.stat().st_blocks<=8,str(p)
   with p.open('rb') as f:
    try:f.seek(0,os.SEEK_DATA)
    except OSError as e:assert e.errno==6
    else:raise AssertionError('Unexpected copied-up data')
   regular+=1;blocks+=p.stat().st_blocks*512
 metadata_same(baseline['cache'])
 INPUT.mkdir();(INPUT/'cache').mkdir()
 (INPUT/'README').write_text('Owned frozen Linux7.1.8 cache private metadata-COW input; source/cache baseline is readonly, only private overlay generated outputs writable. No network/package DB.\n')
 row.update(state='mounted',metadata_promotions=changed,regular_metacopies=regular,regular_metacopy_blocks_bytes=blocks,original_metadata_unchanged=True,free_bytes=os.statvfs(WORK).f_bavail*os.statvfs(WORK).f_frsize)
 assert row['free_bytes']>128*1024**2;save(row);print(json.dumps(row))
if __name__=='__main__':main()
