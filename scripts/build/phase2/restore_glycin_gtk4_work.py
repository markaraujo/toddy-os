"""Restore only the recorded companion scratch bind after its parent volume."""
from pathlib import Path
import fcntl,json,os,re,subprocess,sys

def main():
 name,=sys.argv[1:];assert re.fullmatch(r'[a-z][a-z0-9-]{1,63}',name)
 assert os.geteuid()==0
 subprocess.run(['bash','-c','source /opt/toddy-build/scripts/build/target.sh; guard_target'],check=True)
 lock=open('/var/log/toddy/build/build.lock','a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 assert not list(Path('/var/log/toddy/build').glob('*.running.json'))
 l=Path('/var/log/toddy/phase2');receipt=l/(name+'.json');assert not receipt.exists(),'Reconcile prior restoration; never replay'
 r=json.loads((l/'glycin-gtk4-work-volume.json').read_text());assert r['state']=='mounted'
 parent=Path(r['parent_mount']);backing=Path(r['backing']);work=Path(r['work'])
 assert str(parent)=='/mnt/lfs/sources/phase2/work/glycin-1' and str(backing)==str(parent/'gtk4-companion-work-1') and str(work)=='/mnt/lfs/sources/phase2/work/glycin-gtk4-1'
 assert subprocess.check_output(['findmnt','-n','-o','UUID','--mountpoint',str(parent)],text=True).strip()==r['filesystem_uuid']
 assert not backing.is_symlink() and backing.stat().st_ino==r['backing_inode']
 assert not work.is_symlink() and work.stat().st_ino==r['mountpoint_inode']
 assert subprocess.run(['findmnt','--mountpoint',str(work)],capture_output=True).returncode==1
 subprocess.run(['mount','--bind',str(backing),str(work)],check=True);assert work.stat().st_ino==r['backing_inode']
 result={'state':'complete','scope':'Only existing companion directory bind restored; no filesystem creation/format/trim or accepted compile replay','boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip(),'parent_uuid':r['filesystem_uuid'],'backing_inode':r['backing_inode'],'work':str(work)}
 receipt.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
if __name__=='__main__':main()
