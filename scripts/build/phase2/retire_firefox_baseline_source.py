"""Reproduce the obsolete public source cache before releasing only its inodes."""
from pathlib import Path, PurePosixPath
import fcntl
import hashlib
import json
import os
import shutil
import socket
import subprocess
import sys
import tarfile

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from run_step import snapshot as installed_snapshot
from verify_firefox_security_tree import verify
import restore_browser_work as browser
import restore_firefox_security_source as candidate

BASE=browser.BASE
SOURCE=BASE/'source/firefox-153.2.0'
ARCHIVE=Path('/mnt/lfs/sources/firefox-153.2.0esr.source.tar.xz')
SHA='c443c99704aadaf60fb267d709c42bc283e49e82292084f976369c8327ad833c'
CONTEXT=Path('/var/lib/toddy/phase2-custody/firefox-baseline-source-1')
RECEIPT=Path('/var/log/toddy/phase2/firefox-baseline-source-custody-1.json')


def digest(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()


def save(path,data):
    part=path.with_suffix('.part');assert not part.exists()
    with part.open('x') as f:
        os.fchmod(f.fileno(),0o600);json.dump(data,f,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
    part.replace(path)


def main():
    assert os.geteuid()==0 and socket.gethostname()=='toddy-builder'
    subprocess.run(['bash','-c','source /opt/toddy-build/scripts/build/target.sh; guard_target'],check=True)
    assert subprocess.check_output(['lsblk','-dnro','SERIAL','/dev/vda'],text=True).strip()=='TODDY-BUILDER'
    lock=open('/var/log/toddy/build/build.lock','a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    assert not list(Path('/var/log/toddy/build').glob('*.running.json'))
    assert not CONTEXT.exists() and not RECEIPT.exists(),'Inspect real source/restore/marker; never replay'
    baseline=json.loads(browser.RECORD.read_text());browser.inspect(baseline)
    new=json.loads(candidate.RECEIPT.read_text());candidate.inspect(new)
    assert SOURCE.resolve()==SOURCE and SOURCE.is_dir() and not SOURCE.is_symlink()
    assert not (SOURCE/'.toddy-retired.json').exists()
    assert ARCHIVE.is_file() and not ARCHIVE.is_symlink() and digest(ARCHIVE)==SHA
    old=json.loads(Path('/var/log/toddy/phase2/firefox-source-1.json').read_text())
    assert old['source']['sha256']==SHA and old['members']==509835 and old['expanded_bytes']==3514842428
    assert shutil.disk_usage('/mnt/lfs').free>=16*1024**3
    available=int(next(l.split()[1] for l in Path('/proc/meminfo').read_text().splitlines() if l.startswith('MemAvailable:')))*1024
    assert available>=old['expanded_bytes']+4*1024**3
    mounts=[Path(x) for x in subprocess.check_output(['findmnt','-rn','-o','TARGET'],text=True).splitlines()]
    assert not any(x!=SOURCE and x.is_relative_to(SOURCE) for x in mounts)
    CONTEXT.parent.mkdir(parents=True,mode=0o700,exist_ok=True)
    assert CONTEXT.parent.resolve()==CONTEXT.parent and CONTEXT.parent.stat().st_uid==0 and not CONTEXT.parent.stat().st_mode&0o022
    CONTEXT.mkdir(mode=0o700)
    before=os.statvfs(BASE)
    row={'state':'verifying-old-source','scope':'Obsolete unmodified expanded153.2 public source cache only. Exact bytes/file modes/owners/path set checked against original authenticated archive, then actual filtered restore checked before retirement. Directory timestamps/ACL/xattr byte identity and OS recovery are not claimed. Original archive, old ELF/compiler logs/results, new source/work/tools and installed system retained.',
         'pid':os.getpid(),'start_ticks':Path('/proc/self/stat').read_text().split()[21],'boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip(),
         'producer_sha256':digest(Path(__file__)),'archive':str(ARCHIVE),'archive_sha256':SHA,'source':str(SOURCE),'source_inode':SOURCE.stat().st_ino,
         'before_free_inodes':before.f_favail,'before_browser_free':before.f_bavail*before.f_frsize}
    def record():save(RECEIPT,row)
    def progress(counts):row['progress']=dict(counts);record()
    record();root_before=installed_snapshot();save(CONTEXT/'installed-before.json',root_before)
    original=verify(ARCHIVE,SOURCE,progress,509835,3514842428);row.update(state='restoring-public-source',original=original);record()
    memory=CONTEXT/'restore-memory';memory.mkdir(mode=0o700)
    subprocess.run(['mount','-t','tmpfs','-o','size=6G,noswap,nosuid,nodev,noexec,mode=0700','tmpfs',str(memory)],check=True)
    assert subprocess.check_output(['findmnt','-n','-o','FSTYPE','--mountpoint',str(memory)],text=True).strip()=='tmpfs'
    with tarfile.open(ARCHIVE,mode='r|xz') as bundle:
        for n,member in enumerate(bundle,1):
            parts=PurePosixPath(member.name).parts
            if not parts:assert member.name=='.' and member.isdir();continue
            assert parts[0]==SOURCE.name and '..' not in parts and not member.name.startswith('/')
            bundle.extract(member,memory,filter='data')
            if n%8192==0:row['restore_members']=n;record()
    restored=memory/SOURCE.name;row['state']='verifying-restored-source';record()
    recovered=verify(ARCHIVE,restored,progress,509835,3514842428);assert recovered==original
    assert SOURCE.stat().st_ino==row['source_inode'] and digest(ARCHIVE)==SHA
    row.update(state='restore-verified',restore_exact_in_recorded_scope=True,restored=recovered);record()
    # Only this old source root is made writable after the full recovery proof.
    # The alias remains read-only. The root inode and original mount roles survive.
    row['state']='retiring-obsolete-expanded-source';record()
    subprocess.run(['mount','-o','remount,bind,rw,nosuid,nodev',str(SOURCE)],check=True)
    for p in list(SOURCE.iterdir()):
        row['retiring_child']=p.name;record()
        if p.is_dir() and not p.is_symlink():shutil.rmtree(p)
        else:p.unlink()
    marker={'receipt':str(RECEIPT),'archive':str(ARCHIVE),'archive_sha256':SHA,'recovery':'Extract retained original archive with Python tarfile data filter into a NEW directory, compare complete tree using recorded source verifier/counts. Never overwrite unknown source. Original source cache is no longer present at this retired path.'}
    (SOURCE/'.toddy-retired.json').write_text(json.dumps(marker,indent=2)+'\n')
    subprocess.run(['mount','-o','remount,bind,ro,nosuid,nodev',str(SOURCE)],check=True)
    assert {p.name for p in SOURCE.iterdir()}=={'.toddy-retired.json'} and SOURCE.stat().st_ino==row['source_inode']
    assert installed_snapshot()==root_before,'Installed root changed; preserve state and diagnose'
    browser.inspect(baseline);candidate.inspect(new)
    shutil.rmtree(restored);subprocess.run(['umount',str(memory)],check=True);memory.rmdir()
    after=os.statvfs(BASE);assert after.f_favail>400000 and after.f_bavail*after.f_frsize>=8*1024**3
    row.pop('retiring_child',None);row.update(state='complete',installed_root_changed_paths=0,after_free_inodes=after.f_favail,
          released_inodes=after.f_favail-before.f_favail,after_browser_free=after.f_bavail*after.f_frsize)
    record();print(json.dumps(row))


if __name__=='__main__':main()
