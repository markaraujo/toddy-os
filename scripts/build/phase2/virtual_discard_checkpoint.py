"""Guarded virtual-target free-block reclamation with full content checkpoints."""
import fcntl
import hashlib
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import time

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from run_step import snapshot

LOG=Path('/var/log/toddy/phase2')
RECEIPT=LOG/'virtual-target-discard.json'


def save(path,data,private=False):
    part=path.with_suffix('.part');assert not part.exists()
    with part.open('x') as f:
        if private:os.fchmod(f.fileno(),0o600)
        f.write(json.dumps(data,indent=2)+'\n');f.flush();os.fsync(f.fileno())
    part.replace(path)


def cache_snapshot():
    root=Path('/mnt/lfs/sources/phase2/work/libadwaita-1');result={}
    for p in root.rglob('*'):
        st=p.lstat();row={'mode':st.st_mode,'uid':st.st_uid,'gid':st.st_gid}
        if p.is_symlink():row['link']=str(p.readlink())
        elif p.is_file():
            with p.open('rb') as f:row['sha256']=hashlib.file_digest(f,'sha256').hexdigest()
        result[str(p.relative_to(root))]=row
    assert result;return result


def restore_volumes():
    rows=[]
    for name in ['gtk','desktop-resources','doxygen']+(['glycin'] if (LOG/'glycin-build-volume.json').exists() else []):
        r=json.loads((LOG/(name+'-build-volume.json')).read_text());assert r['state']=='mounted'
        image=Path(r['image']);work=Path(r['work_mount']);st=image.lstat()
        assert image.parent==Path('/var/lib/toddy/phase2-scratch') and image.resolve()==image
        assert stat.S_ISREG(st.st_mode) and st.st_size==r['size_bytes'] and st.st_ino==r['image_inode']
        assert stat.S_IMODE(st.st_mode)==0o600 and not image.is_symlink()
        assert work.parent==Path('/mnt/lfs/sources/phase2/work') and work.resolve()==work and not work.is_symlink()
        assert subprocess.check_output(['blkid','-s','UUID','-o','value',str(image)],text=True).strip()==r['filesystem_uuid']
        mounted=subprocess.run(['mountpoint','-q',str(work)]).returncode
        if mounted==32:
            assert work.is_dir() and not list(work.iterdir()),'Underlying work directory must remain empty before restoration'
            subprocess.run(['mount','-o','loop,nosuid,nodev',str(image),str(work)],check=True)
        else:assert mounted==0
        assert subprocess.check_output(['findmnt','-n','-o','UUID','--mountpoint',str(work)],text=True).strip()==r['filesystem_uuid']
        options=subprocess.check_output(['findmnt','-n','-o','OPTIONS','--mountpoint',str(work)],text=True).strip().split(',')
        assert 'nosuid' in options and 'nodev' in options
        loops=json.loads(subprocess.check_output(['losetup','--json','--list','--output','BACK-FILE','--associated',str(image)],text=True))['loopdevices']
        assert len(loops)==1 and Path(loops[0]['back-file']).resolve()==image
        rows.append({'work':str(work),'uuid':r['filesystem_uuid'],'image_inode':st.st_ino,'restored_existing_filesystem':True})
    return rows


def main():
    action,=sys.argv[1:];assert action in ['before','trim'] and os.getuid()==0
    subprocess.run(['bash','-c','source /opt/toddy-build/scripts/build/target.sh; guard_target'],check=True)
    lock=open('/var/log/toddy/build/build.lock','a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    assert not list(Path('/var/log/toddy/build').glob('*.running.json'))
    boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip()
    if action=='before':
        assert not RECEIPT.exists(),'Reconcile existing maintenance receipt; never replay'
        full=snapshot();pending=cache_snapshot()
        save(LOG/'virtual-target-before-full.json',full,private=True)
        save(LOG/'virtual-target-before-pending-cache.json',pending,private=True)
        r={'scope':'Free-block discard only in designated disposable virtual /dev/vdb4; no formatting, file deletion or physical-host device operation',
           'state':'checkpointed','boot_before':boot,'target_serial':'TODDY-LFS-TARGET','target_root':'/dev/vdb4',
           'full_entries_before':len(full),'pending_cache_entries_before':len(pending),
           'discard_max_before':int(Path('/sys/class/block/vdb/queue/discard_max_bytes').read_text()),'checkpointed_unix':time.time()}
        save(RECEIPT,r);print(json.dumps(r));return
    r=json.loads(RECEIPT.read_text());assert r['state']=='checkpointed' and r['boot_before']!=boot
    r['restored_volumes']=restore_volumes()
    maximum=int(Path('/sys/class/block/vdb/queue/discard_max_bytes').read_text());assert maximum>0,'Virtual discard must be advertised; do not fake success'
    r.update(state='trim_running',boot_after=boot,discard_max_after=maximum);save(RECEIPT,r)
    with (LOG/'virtual-target-discard.log').open('xb') as out:
        result=subprocess.run(['fstrim','--verbose','/mnt/lfs'],stdout=out,stderr=subprocess.STDOUT)
        out.flush();os.fsync(out.fileno())
    (LOG/'virtual-target-discard.exit').write_text(str(result.returncode)+'\n')
    r['trim_exit']=result.returncode;r['state']='trim_done' if result.returncode==0 else 'trim_failed';save(RECEIPT,r)
    assert result.returncode==0
    before=json.loads((LOG/'virtual-target-before-full.json').read_text());after=snapshot()
    pending_before=json.loads((LOG/'virtual-target-before-pending-cache.json').read_text());pending_after=cache_snapshot()
    changed=[p for p in before.keys()|after.keys() if before.get(p)!=after.get(p)]
    cache_changed=[p for p in pending_before.keys()|pending_after.keys() if pending_before.get(p)!=pending_after.get(p)]
    r.update(changed_paths=changed,pending_cache_changed_paths=cache_changed,full_entries_after=len(after),pending_cache_entries_after=len(pending_after))
    r['state']='complete' if not changed and not cache_changed else 'verification_failed';save(RECEIPT,r)
    assert r['state']=='complete','Preserve differences; never repeat trim to hide verification failure'
    print(json.dumps(r))


if __name__=='__main__':main()
