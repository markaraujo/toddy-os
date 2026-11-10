"""Grow the mounted fixed virtual scratch, never reformat or replay an intent."""
from pathlib import Path
import fcntl,hashlib,json,os,subprocess
W=Path('/mnt/lfs/sources/phase2/work/kernel-landlock-1');P=Path('/var/log/toddy/phase2');UUID='c6c4176d-faed-4ee3-9ae0-94914a0af666'
def main():
 assert os.getuid()==0
 subprocess.run(['bash','-c','source /opt/toddy-build/scripts/build/target.sh; guard_target'],check=True)
 lock=open('/var/log/toddy/build/build.lock','a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 assert not list(Path('/var/log/toddy/build').glob('*.running.json')) and (P/'kernel-landlock-build-3.exit').read_text().strip()=='1'
 dest=P/'kernel-landlock-resize-1.json';assert not dest.exists() and not dest.with_suffix('.part').exists(),'Reconcile actual ext4 block count/UUID/log before any recovery'
 device=Path('/dev/disk/by-id/virtio-TODDY-B02-KERNEL').resolve(strict=True)
 assert device.name=='vdc' and Path('/sys/class/block/vdc/serial').read_text().strip()=='TODDY-B02-KERNEL'
 assert int(subprocess.check_output(['blockdev','--getsize64',str(device)],text=True))==1024**3
 assert subprocess.check_output(['findmnt','-n','-o','UUID','--mountpoint',str(W)],text=True).strip()==UUID
 assert hashlib.sha256((W/'baseline.json').read_bytes()).hexdigest()=='d0e66e8e3cc2260d35242a1dca634e72bfd6bcd3d63a5bd94bac591a173114bf'
 config=hashlib.sha256((W/'merged/.config').read_bytes()).hexdigest()
 header=subprocess.check_output(['dumpe2fs','-h',str(device)],stderr=subprocess.DEVNULL,text=True)
 def count(text):return {k.strip():v.strip() for l in text.splitlines() if ':' in l for k,v in [l.split(':',1)]}
 old=count(header);assert int(old['Block count'])*int(old['Block size'])==768*1024**2
 result={'state':'resize-intended','uuid':UUID,'device':str(device),'old_bytes':768*1024**2,'new_bytes':1024**3,'old_block_count':int(old['Block count']),'block_size':int(old['Block size']),'private_config_sha256':config}
 def save():
  part=dest.with_suffix('.part');part.write_text(json.dumps(result,indent=2)+'\n');part.replace(dest)
 save()
 with (P/'kernel-landlock-resize-1.log').open('xb') as log:r=subprocess.run(['resize2fs',str(device)],stdout=log,stderr=subprocess.STDOUT)
 assert r.returncode==0,'Inspect actual geometry; do not replay blindly'
 new=count(subprocess.check_output(['dumpe2fs','-h',str(device)],stderr=subprocess.DEVNULL,text=True));assert int(new['Block count'])*int(new['Block size'])==1024**3
 assert hashlib.sha256((W/'baseline.json').read_bytes()).hexdigest()=='d0e66e8e3cc2260d35242a1dca634e72bfd6bcd3d63a5bd94bac591a173114bf' and hashlib.sha256((W/'merged/.config').read_bytes()).hexdigest()==config
 result.update(state='filesystem-grown',new_block_count=int(new['Block count']),free_bytes=os.statvfs(W).f_bavail*os.statvfs(W).f_frsize,baseline_and_config_unchanged=True);assert result['free_bytes']>128*1024**2;save();print(json.dumps(result))
if __name__=='__main__':main()
