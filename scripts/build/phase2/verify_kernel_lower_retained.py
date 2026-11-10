"""Full original cache postcondition after private COW compilation, no replay."""
from pathlib import Path
import fcntl,hashlib,json,os,subprocess,time
from kernel_cache_baseline import LOWER,WORK,inventory

def main():
 assert os.getuid()==0
 subprocess.run(['bash','-c','source /opt/toddy-build/scripts/build/target.sh; guard_target'],check=True)
 lock=open('/var/log/toddy/build/build.lock','a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 p=Path('/var/log/toddy/phase2');assert not list(Path('/var/log/toddy/build').glob('*.running.json'))
 assert (p/'kernel-landlock-build-4.exit').read_text().strip()=='0'
 dest=p/'kernel-landlock-lower-retained-1.json';assert not dest.exists() and not dest.with_suffix('.part').exists()
 data=(WORK/'baseline.json').read_bytes();assert hashlib.sha256(data).hexdigest()=='d0e66e8e3cc2260d35242a1dca634e72bfd6bcd3d63a5bd94bac591a173114bf'
 r=json.loads(data);start=time.monotonic();actual=inventory(LOWER);assert actual==r['cache'],'Original cache differs after private compile'
 result={'scope':'Full original kernel cache bytes/inodes/modes/UID/GID/size/mtime/link targets unchanged after actual private Landlock compile','unchanged_entries':len(actual),'regular_bytes':r['regular_bytes'],'baseline_sha256':hashlib.sha256(data).hexdigest(),'elapsed_seconds':round(time.monotonic()-start,3),'boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip()}
 part=dest.with_suffix('.part');part.write_text(json.dumps(result,indent=2)+'\n');part.replace(dest);print(json.dumps(result))
if __name__=='__main__':main()
