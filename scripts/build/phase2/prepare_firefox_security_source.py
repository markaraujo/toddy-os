"""Prepare the authenticated Firefox security candidate on existing browser storage."""
from pathlib import Path, PurePosixPath
import fcntl
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tarfile

BASE=Path('/mnt/lfs/sources/phase2/work/firefox-1')
LOG=Path('/var/log/toddy/phase2')
RECEIPT=LOG/'firefox-security-source-1537-1.json'
SHA='7f8715ee7de2cf36a156216a9b1c7f26d1653010e65793bb2fce66e12edb6ea0'
SIZE=800080060
SOURCE=BASE/'source/firefox-153.7.0'
WORK=BASE/'build/browser-security-1537-1'
ARCHIVE=BASE/'security-source-archives/firefox-153.7.0esr.source.tar.xz'
ALIASES=[(ARCHIVE,Path('/mnt/lfs/sources')/ARCHIVE.name,True),
         (SOURCE,SOURCE,True),
         (SOURCE,Path('/mnt/lfs/sources/phase2/inputs/firefox-153.7.0'),True),
         (WORK,Path('/mnt/lfs/sources/phase2/work/firefox-security-1537-1'),False)]


def save(row):
    part=RECEIPT.with_suffix('.part')
    with part.open('x') as f:
        json.dump(row,f,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
    part.replace(RECEIPT)


def main():
    assert os.geteuid()==0
    subprocess.run(['bash','-c','source /opt/toddy-build/scripts/build/target.sh; guard_target'],check=True)
    lock=open('/var/log/toddy/build/build.lock','a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    assert not list(Path('/var/log/toddy/build').glob('*.running.json'))
    assert not RECEIPT.exists() and not RECEIPT.with_suffix('.part').exists(),'Inspect real partial inputs; never replay'
    import restore_browser_work as browser
    browser.inspect(json.loads(browser.RECORD.read_text()))
    assert json.loads((LOG/'firefox-baseline-objects-custody-1.json').read_text())['state']=='complete'
    row=next(r for r in json.loads(Path('/opt/toddy-build/config/phase2/sources.lock.json').read_text())['components'] if r['name']=='firefox-security-1537')
    assert row['version']=='153.7.0esr' and row['sha256']==SHA and row['filename']==ARCHIVE.name
    assert shutil.disk_usage(BASE).free>=9*1024**3
    assert shutil.disk_usage('/mnt/lfs').free>=16*1024**3
    destinations={ARCHIVE.parent,SOURCE,WORK,*(dst for _,dst,_ in ALIASES if dst!=SOURCE)}
    assert all(not os.path.lexists(p) for p in destinations),'Unknown existing candidate path'
    state={'state':'transfer-intended','source':row,'expected_bytes':SIZE,'boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip(),
           'pid':os.getpid(),'start_ticks':Path('/proc/self/stat').read_text().split()[21],
           'source_directory':str(SOURCE),'work_directory':str(WORK),'archive_path':str(ARCHIVE),'aliases':[],
           'scope':'Fresh security source/work only; no old objects, OS installation or runtime acceptance'}
    save(state);ARCHIVE.parent.mkdir(mode=0o755)
    digest=hashlib.sha256();total=0
    with ARCHIVE.open('xb') as f:
        while chunk:=sys.stdin.buffer.read(1024**2):
            total+=len(chunk);assert total<=SIZE;digest.update(chunk);f.write(chunk)
        f.flush();os.fsync(f.fileno())
    assert total==SIZE and digest.hexdigest()==SHA,'Preserve original and incomplete candidate; no extraction'
    ARCHIVE.chmod(0o444)
    state.update(state='extracting',archive_sha256=SHA,archive_bytes=total,members=0,expanded_regular_bytes=0);save(state)
    with tarfile.open(ARCHIVE,mode='r|xz') as bundle:
        for member in bundle:
            parts=PurePosixPath(member.name).parts
            assert parts and parts[0]==SOURCE.name and not member.name.startswith('/') and '..' not in parts
            state['members']+=1
            if member.isfile():state['expanded_regular_bytes']+=member.size
            assert state['expanded_regular_bytes']<=4*1024**3 and state['members']<=520000
            bundle.extract(member,SOURCE.parent,filter='data')
            if state['members']%4096==0:
                assert shutil.disk_usage(BASE).free>=256*1024**2;save(state)
    assert state['members']==510287 and state['expanded_regular_bytes']==3515456965
    assert (SOURCE/'browser/config/version.txt').read_text().strip()=='153.7.0'
    assert (SOURCE/'browser/config/version_display.txt').read_text().strip()=='153.7.0esr'
    critical={}
    for name in ['mach','moz.configure','toolkit/moz.configure','build/moz.configure/rust.configure','python/mozboot/mozboot/util.py','LICENSE']:
        p=SOURCE/name;assert p.is_file() and not p.is_symlink();critical[name]=hashlib.sha256(p.read_bytes()).hexdigest()
    assert 'MINIMUM_RUST_VERSION = "1.90.0"' in (SOURCE/'python/mozboot/mozboot/util.py').read_text()
    WORK.mkdir(mode=0o755);os.chown(WORK,101,101)
    state.update(state='binding-inputs',critical_sha256=critical);save(state)
    for src,dst,ro in ALIASES:
        if src!=dst:
            if src.is_file():dst.touch(mode=0o644,exist_ok=False)
            else:dst.mkdir(mode=0o755)
        state['pending_bind']=str(dst);save(state)
        subprocess.run(['mount','--bind',str(src),str(dst)],check=True)
        subprocess.run(['mount','-o','remount,bind,nosuid,nodev,'+('ro' if ro else 'rw'),str(dst)],check=True)
        assert src.stat().st_ino==dst.stat().st_ino
        state['aliases'].append({'source':str(src),'target':str(dst),'readonly':ro,'inode':src.stat().st_ino})
    state.pop('pending_bind');state.update(state='prepared',available_browser_bytes=shutil.disk_usage(BASE).free)
    assert state['available_browser_bytes']>=4*1024**3
    save(state);print(json.dumps(state))


if __name__=='__main__':main()
