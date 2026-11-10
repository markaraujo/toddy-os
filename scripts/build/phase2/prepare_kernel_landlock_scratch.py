"""Format only the blank, fixed B02 virtual scratch after recording its UUID.

Any existing receipt refuses replay, including interrupted mkfs/mount. Reconcile
actual blkid/mount state against the recorded intended UUID before recovery.
"""
from pathlib import Path
import fcntl,json,os,stat,subprocess,uuid

DEVICE=Path('/dev/disk/by-id/virtio-TODDY-B02-KERNEL')
BYTES=768*1024**2
WORK=Path('/mnt/lfs/sources/phase2/work/kernel-landlock-1')
RECEIPT=Path('/var/log/toddy/phase2/kernel-landlock-scratch-1.json')

def validate_identity(row):
 assert row['type']=='disk' and row['serial']=='TODDY-B02-KERNEL'
 assert row['size']==BYTES and row['ro'] is False
 assert not row.get('children') and not row.get('fstype') and not row.get('uuid')
 assert all(x is None for x in row['mountpoints'])
 assert row['path'] not in ['/dev/vda','/dev/vdb']

def save(row):
 part=RECEIPT.with_suffix('.part');assert not part.exists()
 with part.open('x') as f:
  f.write(json.dumps(row,indent=2)+'\n');f.flush();os.fsync(f.fileno())
 part.replace(RECEIPT)

def main():
 assert os.getuid()==0
 subprocess.run(['bash','-c','source /opt/toddy-build/scripts/build/target.sh; guard_target'],check=True)
 lock=open('/var/log/toddy/build/build.lock','a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 assert not list(Path('/var/log/toddy/build').glob('*.running.json'))
 assert not RECEIPT.exists() and not RECEIPT.with_suffix('.part').exists(),'Reconcile intended UUID and actual state; NEVER repeat mkfs'
 assert not WORK.exists(),'Inspect existing work/mount before any mutation'
 target=DEVICE.resolve(strict=True);st=target.stat();assert stat.S_ISBLK(st.st_mode)
 assert (Path('/sys/class/block')/target.name/'serial').read_text().strip()=='TODDY-B02-KERNEL'
 data=json.loads(subprocess.check_output(['lsblk','--json','--bytes','--output','PATH,SERIAL,SIZE,TYPE,FSTYPE,UUID,MOUNTPOINTS,RO',str(target)],text=True))['blockdevices'];assert len(data)==1
 row=data[0];validate_identity(row)
 assert not subprocess.check_output(['wipefs','--no-act','--noheadings',str(target)],text=True).strip()
 # Read every byte. No magic-only blank assumption or force-format flag.
 count=0
 with target.open('rb',buffering=0) as f:
  while chunk:=f.read(4*1024**2):
   assert not any(chunk),'Scratch contains data; refuse format';count+=len(chunk)
 assert count==BYTES
 result={'state':'blank-verified-format-intended','scope':'Only fixed dedicated virtual scratch, not target root/physical disk','device':str(target),'major_minor':[os.major(st.st_rdev),os.minor(st.st_rdev)],'serial':row['serial'],'bytes':BYTES,'blank_bytes_verified':count,'intended_uuid':str(uuid.uuid4()),'work':str(WORK),'boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip()}
 save(result)
 with RECEIPT.with_suffix('.mkfs.log').open('xb') as log:
  run=subprocess.run(['mkfs.ext4','-U',result['intended_uuid'],'-L','TODDY-B02-KERNEL','-m','0','-E','nodiscard,lazy_itable_init=0,lazy_journal_init=0',str(target)],stdout=log,stderr=subprocess.STDOUT)
 assert run.returncode==0,'Inspect actual UUID/log; do NOT rerun mkfs'
 assert subprocess.check_output(['blkid','-s','UUID','-o','value',str(target)],text=True).strip()==result['intended_uuid']
 result['state']='formatted-mount-pending';save(result)
 WORK.mkdir();subprocess.run(['mount','-o','nosuid,nodev',str(target),str(WORK)],check=True)
 assert subprocess.check_output(['findmnt','-n','-o','UUID','--mountpoint',str(WORK)],text=True).strip()==result['intended_uuid']
 opts=subprocess.check_output(['findmnt','-n','-o','OPTIONS','--mountpoint',str(WORK)],text=True).strip().split(',');assert 'nosuid' in opts and 'nodev' in opts
 os.chown(WORK,101,101)
 result.update(state='mounted',free_bytes=os.statvfs(WORK).f_bavail*os.statvfs(WORK).f_frsize)
 assert result['free_bytes']>128*1024**2;save(result);print(json.dumps(result))
if __name__=='__main__':main()
