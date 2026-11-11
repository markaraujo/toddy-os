"""Retain the original archive on browser storage without consuming target reserve."""
from pathlib import Path
import fcntl
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import restore_browser_work as browser

LOG=Path('/var/log/toddy/phase2')
RECORD=LOG/'firefox-baseline-archive-relocation-1.json'
SOURCE=Path('/mnt/lfs/sources/firefox-153.2.0esr.source.tar.xz')
BACKUP=SOURCE.with_name(SOURCE.name+'.relocation-1-original')
STORED=browser.BASE/'security-source-archives'/SOURCE.name
SHA='c443c99704aadaf60fb267d709c42bc283e49e82292084f976369c8327ad833c'
SIZE=807705672


def digest(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()


def sync_directory(path):
    fd=os.open(path,os.O_RDONLY|os.O_DIRECTORY)
    try:os.fsync(fd)
    finally:os.close(fd)


def save(path,row):
    part=path.with_suffix('.part');assert not part.exists()
    with part.open('x') as f:json.dump(row,f,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
    part.replace(path);sync_directory(path.parent)


def inspect():
    r=json.loads(RECORD.read_text());assert r['state']=='complete'
    assert r['archive_sha256']==SHA and r['archive_bytes']==SIZE
    assert STORED.resolve()==STORED and not STORED.is_symlink() and STORED.is_file() and STORED.stat().st_size==SIZE and digest(STORED)==SHA
    assert SOURCE.is_file() and not SOURCE.is_symlink() and SOURCE.stat().st_ino==STORED.stat().st_ino
    options=set(subprocess.check_output(['findmnt','-n','-o','OPTIONS','--mountpoint',str(SOURCE)],text=True).strip().split(','))
    assert {'ro','nosuid','nodev'}<=options and digest(SOURCE)==SHA
    assert not os.path.lexists(BACKUP)
    return {'state':'inspected','archive_sha256':SHA,'same_inode':True,'readonly_alias':True}


def main():
    assert os.geteuid()==0 and (sys.argv[1:] in [[],['--inspect']] or len(sys.argv)==3 and sys.argv[1]=='--restore')
    subprocess.run(['bash','-c','source /opt/toddy-build/scripts/build/target.sh; guard_target'],check=True)
    l=open('/var/log/toddy/build/build.lock','a');fcntl.flock(l,fcntl.LOCK_EX|fcntl.LOCK_NB)
    assert not list(Path('/var/log/toddy/build').glob('*.running.json'))
    browser.inspect(json.loads(browser.RECORD.read_text()))
    if sys.argv[1:]==['--inspect']:print(json.dumps(inspect()));return
    restoring=len(sys.argv)==3
    if restoring:
        name=sys.argv[2];assert re.fullmatch('[a-z0-9][a-z0-9-]{1,90}',name)
        receipt=LOG/(name+'.json');assert not receipt.exists() and not receipt.with_suffix('.part').exists(),'Inspect actual mounts; never replay'
        old=json.loads(RECORD.read_text());assert old['state']=='complete' and old['archive_sha256']==SHA
        assert SOURCE.is_file() and not SOURCE.is_symlink() and SOURCE.stat().st_size==0
        assert not os.path.lexists(BACKUP) and STORED.is_file() and not STORED.is_symlink() and digest(STORED)==SHA
        r={'state':'restoring-existing-alias','boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip()};save(receipt,r)
    else:
        assert all(not os.path.lexists(p) for p in [RECORD,STORED,BACKUP]),'Inspect prior relocation; never replay'
        assert not subprocess.run(['mountpoint','-q',str(SOURCE)]).returncode==0
        assert SOURCE.is_file() and not SOURCE.is_symlink() and SOURCE.stat().st_size==SIZE and digest(SOURCE)==SHA
        assert json.loads((LOG/'firefox-baseline-source-custody-1.json').read_text())['state']=='complete'
        assert shutil.disk_usage(browser.BASE).free>=SIZE+512*1024**2
        r={'state':'copying-verified-archive','archive_sha256':SHA,'archive_bytes':SIZE,'original_inode':SOURCE.stat().st_ino,
           'before_target_free':shutil.disk_usage('/mnt/lfs').free,'scope':'Source-cache storage only; no installed package or source-byte change'}
        receipt=RECORD;save(receipt,r)
        with SOURCE.open('rb') as src,STORED.open('xb') as dst:
            shutil.copyfileobj(src,dst,1024**2);os.fchmod(dst.fileno(),0o444);dst.flush();os.fsync(dst.fileno())
        sync_directory(STORED.parent);assert STORED.stat().st_size==SIZE and digest(STORED)==SHA
        r['state']='switching-to-readonly-alias';save(receipt,r)
        SOURCE.rename(BACKUP);SOURCE.touch(mode=0o444,exist_ok=False);sync_directory(SOURCE.parent)
    subprocess.run(['mount','--bind',str(STORED),str(SOURCE)],check=True)
    subprocess.run(['mount','-o','remount,bind,ro,nosuid,nodev',str(SOURCE)],check=True)
    assert SOURCE.stat().st_ino==STORED.stat().st_ino and digest(SOURCE)==SHA
    if not restoring:
        assert BACKUP.stat().st_ino==r['original_inode'] and digest(BACKUP)==SHA
        r['state']='retiring-verified-duplicate';save(receipt,r);BACKUP.unlink();sync_directory(SOURCE.parent)
        r.update(state='complete',after_target_free=shutil.disk_usage('/mnt/lfs').free)
        assert r['after_target_free']>=r['before_target_free']+SIZE-2*1024**2
        save(receipt,r)
    else:r.update(state='complete');save(receipt,r)
    assert inspect()['readonly_alias'];print(json.dumps(r))


if __name__=='__main__':main()
