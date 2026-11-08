"""Create one bounded regular-file build volume in the disposable builder VM."""
import fcntl
import json
import os
from pathlib import Path
import stat
import subprocess
import uuid


def main():
    subprocess.run(['bash','-c','source /opt/toddy-build/scripts/build/target.sh; guard_target'],check=True)
    lock=open('/var/log/toddy/build/build.lock','a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    assert not list(Path('/var/log/toddy/build').glob('*.running.json'))
    receipt=Path('/var/log/toddy/phase2/glycin-build-volume.json')
    assert not receipt.exists(),'Reconcile actual image/filesystem/mount/receipt; never repeat uncertain provisioning'
    work=Path('/mnt/lfs/sources/phase2/work/glycin-1')
    assert not work.exists() and not work.is_symlink(),'Reconcile preallocated work, never repeat uncertain provisioning'
    assert work.parent.resolve()==work.parent and work.parent.is_dir()
    work.mkdir();os.chown(work,101,101)
    assert subprocess.run(['mountpoint','-q',str(work)]).returncode==32
    base=Path('/var/lib/toddy/phase2-scratch');base.mkdir(parents=True,exist_ok=True,mode=0o700)
    assert base.resolve()==base and not base.is_symlink()
    image=base/'glycin-1.ext4';assert not image.exists() and not image.is_symlink()
    size=2560*1024**2;fs=os.statvfs(base);assert fs.f_bavail*fs.f_frsize>=size+1024**3
    identity=str(uuid.uuid4())
    r={'scope':'Bounded compiler scratch only, regular file in disposable builder VM; not an installation target or physical disk',
       'image':str(image),'work_mount':str(work),'size_bytes':size,'filesystem_uuid':identity,'label':'TODDY_GLY_BUILD','state':'planned'}
    def save():
        part=receipt.with_suffix('.part');assert not part.exists()
        with part.open('x') as output:output.write(json.dumps(r,indent=2)+'\n');output.flush();os.fsync(output.fileno())
        part.replace(receipt)
    save()
    with image.open('xb') as output:output.truncate(size);output.flush();os.fsync(output.fileno())
    image.chmod(0o600);assert stat.S_ISREG(image.lstat().st_mode) and image.stat().st_size==size
    r['image_inode']=image.stat().st_ino;r['state']='created';save()
    subprocess.run(['mkfs.ext4','-F','-m','0','-L',r['label'],'-U',identity,str(image)],check=True)
    assert subprocess.check_output(['blkid','-s','UUID','-o','value',str(image)],text=True).strip()==identity
    r['state']='formatted';save()
    subprocess.run(['mount','-o','loop,nosuid,nodev',str(image),str(work)],check=True)
    assert subprocess.check_output(['findmnt','-n','-o','UUID','--mountpoint',str(work)],text=True).strip()==identity
    backing=json.loads(subprocess.check_output(['losetup','--json','--list','--output','BACK-FILE','--associated',str(image)],text=True))
    assert len(backing['loopdevices'])==1 and Path(backing['loopdevices'][0]['back-file']).resolve()==image
    (work/'lost+found').rmdir();os.chown(work,101,101);work.chmod(0o755)
    r['state']='mounted';r['owner_uid']=101;r['mount_options']=subprocess.check_output(['findmnt','-n','-o','OPTIONS','--mountpoint',str(work)],text=True).strip()
    assert 'nosuid' in r['mount_options'] and 'nodev' in r['mount_options']
    r['recovery']='After guest restart inspect image UUID and complete mount postcondition before remounting this same file; never reformat. Preserve contents/logs/compiled tests.'
    save();print(json.dumps(r))


if __name__=='__main__':main()
