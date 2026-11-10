"""Read-only kernel/source inventory saved only on the dedicated build scratch."""
from pathlib import Path
import fcntl,hashlib,json,os,stat,subprocess,tarfile,time

LOWER=Path('/mnt/lfs/sources/linux-7.1.8')
WORK=Path('/mnt/lfs/sources/phase2/work/kernel-landlock-1')

def digest(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def inventory(base):
 rows={}
 for p in [base,*base.rglob('*')]:
  s=p.lstat();r={'mode':s.st_mode,'uid':s.st_uid,'gid':s.st_gid,'inode':s.st_ino,'size':s.st_size,'mtime_ns':s.st_mtime_ns}
  if stat.S_ISREG(s.st_mode):r['sha256']=digest(p)
  elif stat.S_ISLNK(s.st_mode):r['link']=os.readlink(p)
  else:assert stat.S_ISDIR(s.st_mode),'Unexpected kernel cache special file'
  rows[str(p.relative_to(base))]=r
 return rows

def main():
 assert os.getuid()==0
 subprocess.run(['bash','-c','source /opt/toddy-build/scripts/build/target.sh; guard_target'],check=True)
 lock=open('/var/log/toddy/build/build.lock','a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 assert not list(Path('/var/log/toddy/build').glob('*.running.json'))
 dest=WORK/'baseline.json';assert not dest.exists() and not dest.with_suffix('.part').exists(),'Reconcile existing baseline; do not replay'
 receipt=json.loads(Path('/var/log/toddy/phase2/kernel-landlock-scratch-1.json').read_text());assert receipt['state']=='mounted'
 assert subprocess.check_output(['findmnt','-n','-o','UUID','--mountpoint',str(WORK)],text=True).strip()==receipt['intended_uuid']
 assert LOWER.is_dir() and not LOWER.is_symlink() and LOWER.stat().st_ino==7523763
 assert subprocess.check_output(['chroot','/mnt/lfs','dpkg-query','-W','-f=${Status} ${Version}','linux-kernel'],text=True)=='install ok installed 7.1.8-1'
 assert (LOWER/'.config').read_bytes()==Path('/mnt/lfs/boot/config-7.1.8-toddy').read_bytes()
 assert (LOWER/'arch/x86/boot/bzImage').read_bytes()==Path('/mnt/lfs/boot/vmlinuz-7.1.8-toddy').read_bytes()
 source=next(r for r in json.loads(Path('/opt/toddy-build/config/sources.lock.json').read_text())['packages'] if r['filename']=='linux-7.1.8.tar.xz')
 archive=LOWER.parent/source['filename'];assert digest(archive)==source['sha256']
 started=time.monotonic();cache=inventory(LOWER);pristine={}
 with tarfile.open(archive) as t:
  for m in t:
   p=Path(m.name);assert p.parts[0]=='linux-7.1.8' and not p.is_absolute() and '..' not in p.parts
   key=str(Path(*p.parts[1:]))
   if m.isfile():
    actual=hashlib.file_digest(t.extractfile(m),'sha256').hexdigest();assert cache[key]['sha256']==actual,('Modified frozen source',key);pristine[key]={'sha256':actual}
   elif m.issym():
    actual=cache[key]['link']
    if actual!=m.linkname:
     assert key=='tools/testing/selftests/powerpc/primitives/asm/asm-compat.h'
     assert m.linkname=='../.././../../../../arch/powerpc/include/asm/asm-compat.h'
     assert actual=='../../../../../../arch/powerpc/include/asm/asm-compat.h'
     assert os.path.normpath(str((LOWER/key).parent/m.linkname))==os.path.normpath(str((LOWER/key).parent/actual))
    pristine[key]={'link':actual,'archive_link':m.linkname}
   else:assert m.isdir(),'Unexpected archive member'
 assert pristine and len(cache)>len(pristine)
 result={'scope':'Full immutable original Linux7.1.8 cache bytes/metadata and pristine frozen source inventory, no lower writes or config change. Only baseline output on dedicated scratch.','source':source,'lower_inode':LOWER.stat().st_ino,'owned_package':'linux-kernel 7.1.8-1','installed_config_and_image_identical':True,'pristine_source':pristine,'cache':cache,'cache_entries':len(cache),'regular_bytes':sum(x['size'] for x in cache.values() if 'sha256' in x),'elapsed_seconds':round(time.monotonic()-started,3),'boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip()}
 part=dest.with_suffix('.part')
 with part.open('x') as f:f.write(json.dumps(result,separators=(',',':'))+'\n');f.flush();os.fsync(f.fileno())
 part.rename(dest);print(json.dumps({k:v for k,v in result.items() if k not in ('cache','pristine_source')},indent=2))
 assert os.statvfs(WORK).f_bavail*os.statvfs(WORK).f_frsize>128*1024**2
if __name__=='__main__':main()
