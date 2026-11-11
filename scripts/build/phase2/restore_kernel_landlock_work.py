"""Restore only the existing qualified kernel scratch/COW mounts after cold boot."""
from pathlib import Path
import fcntl,hashlib,json,os,re,subprocess,sys
W=Path('/mnt/lfs/sources/phase2/work/kernel-landlock-1');LOWER=Path('/mnt/lfs/sources/linux-7.1.8');UUID='c6c4176d-faed-4ee3-9ae0-94914a0af666';L=Path('/var/log/toddy/phase2')
def mounted(path):return subprocess.run(['findmnt','--mountpoint',str(path)],capture_output=True).returncode==0
def inspect():
 assert subprocess.check_output(['findmnt','-n','-o','UUID','--mountpoint',str(W)],text=True).strip()==UUID
 assert hashlib.sha256((W/'baseline.json').read_bytes()).hexdigest()=='d0e66e8e3cc2260d35242a1dca634e72bfd6bcd3d63a5bd94bac591a173114bf'
 private=W/'private-overlay';assert private.stat().st_uid==0 and private.stat().st_mode&0o777==0o700
 assert LOWER.stat().st_ino==7523763 and not LOWER.is_symlink()
 assert subprocess.check_output(['findmnt','-n','-o','FSTYPE','--mountpoint',str(W/'merged')],text=True).strip()=='overlay'
 assert 'ro' in subprocess.check_output(['findmnt','-n','-o','OPTIONS','--mountpoint',str(private/'lower')],text=True).strip().split(',')
 assert (private/'lower').stat().st_ino==LOWER.stat().st_ino
 assert (W/'merged').stat().st_uid==101
 return {'scope':'Existing qualified raw scratch and private COW only; no format/resize/extraction/chown or stage/compile replay','uuid':UUID,'lower_inode':LOWER.stat().st_ino,'private_upper_inode':(private/'upper').stat().st_ino,'private_work_inode':(private/'work').stat().st_ino,'boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip()}
def main():
 assert os.getuid()==0
 subprocess.run(['bash','-c','source /opt/toddy-build/scripts/build/target.sh; guard_target'],check=True)
 lock=open('/var/log/toddy/build/build.lock','a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 assert not list(Path('/var/log/toddy/build').glob('*.running.json'))
 if sys.argv[1:]==['--inspect']:print(json.dumps(inspect()));return
 name,=sys.argv[1:];assert re.fullmatch(r'[a-z][a-z0-9-]{1,63}',name)
 receipt=L/(name+'.json');assert not receipt.exists() and not receipt.with_suffix('.part').exists(),'Inspect existing mounts/receipt before any restoration replay'
 assert not mounted(W) and W.is_dir() and not W.is_symlink() and not list(W.iterdir())
 device=Path('/dev/disk/by-id/virtio-TODDY-B02-KERNEL').resolve(strict=True)
 assert device.name=='vdc' and Path('/sys/class/block/vdc/serial').read_text().strip()=='TODDY-B02-KERNEL'
 size=int(subprocess.check_output(['blockdev','--getsize64',str(device)],text=True))
 assert size in [1024**3,2*1024**3]
 if size==2*1024**3:
  growth=json.loads((L/'kernel-fuse-resize-1.json').read_text());assert growth['state']=='filesystem-grown' and growth['new_bytes']==size and growth['uuid']==UUID
 assert subprocess.check_output(['blkid','-s','UUID','-o','value',str(device)],text=True).strip()==UUID
 row={'state':'restore-intended','device':str(device),'uuid':UUID,'work':str(W)}
 def save():
  part=receipt.with_suffix('.part');part.write_text(json.dumps(row,indent=2)+'\n');part.replace(receipt)
 save();subprocess.run(['mount','-o','nosuid,nodev',str(device),str(W)],check=True)
 private=W/'private-overlay';assert private.stat().st_uid==0 and private.stat().st_mode&0o777==0o700
 assert not mounted(private/'lower') and not mounted(W/'merged') and not list((private/'lower').iterdir())
 assert LOWER.stat().st_ino==7523763
 subprocess.run(['mount','--bind',str(LOWER),str(private/'lower')],check=True)
 subprocess.run(['mount','-o','remount,bind,ro,nosuid,nodev',str(private/'lower')],check=True)
 subprocess.run(['mount','-t','overlay','overlay','-o',f'lowerdir={private}/lower,upperdir={private}/upper,workdir={private}/work,metacopy=on,index=off',str(W/'merged')],check=True)
 row.update(inspect());row['state']='complete';row['native_stage_alias']='Closed completed package stage bind intentionally not restored; payload/archive already qualified and data retained at work/stage';save();print(json.dumps(row))
if __name__=='__main__':main()
