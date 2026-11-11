"""Prepare frozen Nautilus source/worker on the verified existing build tmpfs."""
import errno
import fcntl
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tarfile

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from source_filter import source_filter,validate_source_members
ROOT=Path('/opt/toddy-build');TARGET=Path('/mnt/lfs');BASE=Path('/run/toddy-samba-client-1');LOG=Path('/var/log/toddy/phase2')


def digest(path):
    with path.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()


def free(path):
    s=os.statvfs(path);return s.f_bavail*s.f_frsize


def main():
    assert os.geteuid()==0
    subprocess.run(['bash','-c','source /opt/toddy-build/scripts/build/target.sh; guard_target'],check=True)
    lock=open('/var/log/toddy/build/build.lock','a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    assert not list(Path('/var/log/toddy/build').glob('*.running.json'))
    recovery=json.loads((LOG/'localsearch4-scratch-restored-1.json').read_text());assert recovery['state']=='complete'
    assert recovery['boot_id']==Path('/proc/sys/kernel/random/boot_id').read_text().strip()
    assert subprocess.check_output(['findmnt','-n','-o','FSTYPE','--mountpoint',str(BASE)],text=True).strip()=='tmpfs'
    assert os.statvfs(BASE).f_blocks*os.statvfs(BASE).f_frsize==2*1024**3
    assert {'nosuid','nodev'}<=set(subprocess.check_output(['findmnt','-n','-o','OPTIONS','--mountpoint',str(BASE)],text=True).strip().split(','))
    assert free(BASE)>=512*1024**2 and free(TARGET)>=16*1024**3+1024**2
    for step in ['b02-localsearch-install','b02-localsearch-schema-union-install']:
        r=json.loads(Path('/var/log/toddy/build',step+'.success.json').read_text());assert r['recipe_exit']==r['postcheck_exit']==0
    row=next(r for r in json.loads((ROOT/'config/phase2/sources.lock.json').read_text())['components'] if r['name']=='nautilus')
    assert row['version']=='50.2.2' and row['sha256']=='e1e285efddf42ed30dda5b29f7f8d242dab4bc1409a9054863b367bad4b34d5a'
    holder=BASE/'nautilus-input-1';source=holder/'nautilus-50.2.2';work=BASE/'nautilus-work-1'
    source_alias=TARGET/'sources/phase2/inputs/nautilus-50.2.2';work_alias=TARGET/'sources/phase2/work/nautilus-1'
    receipt=LOG/'nautilus-input-tmpfs-1.json'
    assert not any(os.path.lexists(p) for p in [holder,work,source_alias,work_alias,receipt,receipt.with_suffix('.part')])
    query=subprocess.run(['chroot',str(TARGET),'dpkg-query','-W','-f=${Status}','nautilus'],capture_output=True,text=True);assert query.returncode==1
    state={'state':'planned','source':row,'boot_id':recovery['boot_id'],'mount_id':subprocess.check_output(['findmnt','-n','-o','ID','--mountpoint',str(BASE)],text=True).strip(),'target_free_before':free(TARGET),'source_alias':str(source_alias),'work_alias':str(work_alias)}
    def save():
        part=receipt.with_suffix('.part')
        with part.open('x') as f:json.dump(state,f,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
        part.replace(receipt)
    save();holder.mkdir(mode=0o755)
    archive=holder/row['filename'];h=hashlib.sha256();size=0
    with archive.open('xb') as f:
        while chunk:=sys.stdin.buffer.read(1024**2):
            size+=len(chunk);assert size<=8*1024**2;h.update(chunk);f.write(chunk)
    assert h.hexdigest()==row['sha256']
    with tarfile.open(archive) as bundle:
        members=bundle.getmembers();assert members and all(Path(m.name).parts[0]=='nautilus-50.2.2' for m in members)
        expanded=sum(m.size for m in members if m.isfile());assert expanded<=64*1024**2
        validate_source_members(archive.name,members);checked=source_filter(archive.name)
        for member in members:checked(member,holder)
        bundle.extractall(holder,filter=checked)
    recipe=ROOT/'scripts/build/phase2/nautilus-build.sh';(source/'toddy-build.sh').write_bytes(recipe.read_bytes())
    prepared={'source_sha256':row['sha256'],'recipe_sha256':digest(recipe),'source_patches':[],'book':'BLFS13.1-systemd gnome/nautilus.html','book_page_sha256':'a68a45f372ce35ddc351ea1769e2c84ce2709719502ea4aa1121b0e1563da5f8','scope':'No source patches/fallback downloads; actual source glycin>=2 uses the already qualified owned2.1SDK, all original tests compiled for native graphical qualification.'}
    (source/'toddy-prepared.json').write_text(json.dumps(prepared,indent=2)+'\n')
    work.mkdir(mode=0o755);os.chown(work,101,101)
    bindings=[(source,source_alias,True),(work,work_alias,False)]
    archive_alias=TARGET/'sources'/row['filename']
    if archive_alias.exists():assert digest(archive_alias)==row['sha256']
    else:archive_alias.touch(mode=0o644);bindings.append((archive,archive_alias,True))
    state['bindings']=[]
    for src,dst,readonly in bindings:
        if src.is_dir():dst.mkdir(mode=0o755)
        state['pending_bind']=str(dst);save()
        subprocess.run(['mount','--bind',str(src),str(dst)],check=True)
        flags='remount,bind,nosuid,nodev'+(',ro' if readonly else ',rw')+(',noexec' if src.is_file() else '')
        subprocess.run(['mount','-o',flags,str(dst)],check=True)
        actual=set(subprocess.check_output(['findmnt','-n','-o','OPTIONS','--mountpoint',str(dst)],text=True).strip().split(','));assert {'nosuid','nodev','ro' if readonly else 'rw'}<=actual
        assert src.stat().st_ino==dst.stat().st_ino
        state['bindings'].append({'source':str(src),'target':str(dst),'readonly':readonly});state.pop('pending_bind');save()
    try:fd=os.open(source_alias/'.toddy-write-denial',os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
    except OSError as e:assert e.errno==errno.EROFS
    else:os.close(fd);raise AssertionError('Source unexpectedly writable')
    assert free(BASE)>=384*1024**2 and free(TARGET)>=16*1024**3
    state.update(state='prepared',source_inode=source.stat().st_ino,work_inode=work.stat().st_ino,expanded_source_bytes=expanded,prepared_sha256=digest(source/'toddy-prepared.json'),scratch_free=free(BASE),target_free=free(TARGET),root_source_write_denied=True)
    save();print(json.dumps(state))


if __name__=='__main__':main()
