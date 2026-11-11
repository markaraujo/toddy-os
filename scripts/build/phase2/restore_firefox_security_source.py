"""Inspect or restore only recorded existing Firefox security-candidate mounts."""
from pathlib import Path
import fcntl
import hashlib
import json
import os
import re
import subprocess
import sys
from prepare_firefox_security_source import BASE,LOG,RECEIPT,SHA,SIZE,SOURCE,WORK,ARCHIVE,ALIASES
import restore_browser_work as browser


def digest(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()


def mounted(p):
    return subprocess.run(['findmnt','--mountpoint',str(p)],capture_output=True).returncode==0


def inputs(record):
    browser.inspect(json.loads(browser.RECORD.read_text()))
    assert record['state']=='prepared' and record['archive_path']==str(ARCHIVE)
    assert record['source_directory']==str(SOURCE) and record['work_directory']==str(WORK)
    for p in [SOURCE,WORK,ARCHIVE]:assert p.resolve()==p and not p.is_symlink()
    assert ARCHIVE.stat().st_size==SIZE and digest(ARCHIVE)==SHA
    assert WORK.stat().st_uid==WORK.stat().st_gid==101
    for name,expected in record['critical_sha256'].items():
        p=SOURCE/name;assert p.resolve().is_relative_to(SOURCE) and not p.is_symlink() and digest(p)==expected
    assert [(r['source'],r['target'],r['readonly']) for r in record['aliases']]==[(str(s),str(d),ro) for s,d,ro in ALIASES]
    for row,(src,_,_) in zip(record['aliases'],ALIASES):assert src.stat().st_ino==row['inode']


def inspect(record):
    inputs(record)
    for src,dst,ro in ALIASES:
        assert mounted(dst) and src.stat().st_ino==dst.stat().st_ino
        options=set(subprocess.check_output(['findmnt','-n','-o','OPTIONS','--mountpoint',str(dst)],text=True).strip().split(','))
        assert {'ro' if ro else 'rw','nosuid','nodev'}<=options
    return {'state':'inspected','aliases':record['aliases'],'critical_sha256':record['critical_sha256'],'archive_sha256':SHA}


def main():
    assert os.geteuid()==0 and len(sys.argv)==2
    subprocess.run(['bash','-c','source /opt/toddy-build/scripts/build/target.sh; guard_target'],check=True)
    lock=open('/var/log/toddy/build/build.lock','a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    assert not list(Path('/var/log/toddy/build').glob('*.running.json'))
    record=json.loads(RECEIPT.read_text())
    if sys.argv[1]=='--inspect':print(json.dumps(inspect(record)));return
    name=sys.argv[1];assert re.fullmatch(r'[a-z0-9][a-z0-9-]{1,90}',name)
    receipt=LOG/(name+'.json');assert not receipt.exists() and not receipt.with_suffix('.part').exists(),'Inspect actual mounts; never replay'
    inputs(record)
    assert all(not mounted(dst) for _,dst,_ in ALIASES),'Partial/existing mounts require diagnosis'
    for src,dst,_ in ALIASES:
        if src==dst:continue
        assert not dst.is_symlink()
        assert dst.is_file() and dst.stat().st_size==0 or dst.is_dir() and not list(dst.iterdir())
    state={'state':'restoring-existing-mounts','boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip(),'aliases':[]}
    def save():
        part=receipt.with_suffix('.part')
        with part.open('x') as f:json.dump(state,f,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
        part.replace(receipt)
    save()
    for src,dst,ro in ALIASES:
        state['pending_bind']=str(dst);save()
        subprocess.run(['mount','--bind',str(src),str(dst)],check=True)
        subprocess.run(['mount','-o','remount,bind,nosuid,nodev,'+('ro' if ro else 'rw'),str(dst)],check=True)
        state['aliases'].append(str(dst));save()
    state.pop('pending_bind');state.update(state='complete',inspection=inspect(record));save();print(json.dumps(state))


if __name__=='__main__':main()
