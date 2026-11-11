"""Prepare the browser's private NASM build using the verified browser disk."""
from pathlib import Path
import fcntl
import hashlib
import json
import os
import subprocess
import sys
import tarfile


def main():
    assert os.geteuid() == 0
    subprocess.run(['bash','-c','source /opt/toddy-build/scripts/build/target.sh; guard_target'],check=True)
    lock=open('/var/log/toddy/build/build.lock','a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    assert not list(Path('/var/log/toddy/build').glob('*.running.json'))
    base=Path('/mnt/lfs/sources/phase2/work/firefox-1')
    volume=json.loads(Path('/var/log/toddy/phase2/firefox-work-volume-1.json').read_text())
    assert subprocess.check_output(['findmnt','-n','-o','UUID','--mountpoint',str(base)],text=True).strip()==volume['filesystem_uuid']
    source=base/'source/nasm-3.02';work=base/'build/nasm-1'
    source_alias=Path('/mnt/lfs/sources/phase2/inputs/nasm-3.02')
    work_alias=Path('/mnt/lfs/sources/phase2/work/nasm-1')
    receipt=Path('/var/log/toddy/phase2/nasm-input-1.json')
    assert not any(os.path.lexists(p) for p in [source,work,source_alias,work_alias,receipt,receipt.with_suffix('.part')])
    row=next(r for r in json.loads(Path('/opt/toddy-build/config/phase2/sources.lock.json').read_text())['components'] if r['name']=='nasm')
    assert row['version']=='3.02' and row['sha256']=='87336eba53b4acfe917424ab5d500d2b0054d9f5148d35c2273ccf2cfb712f0d'
    archive=base/'source'/row['filename'];assert not archive.exists()
    state=dict(state='transfer-intended',source=row,boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip())
    def save():
        with receipt.with_suffix('.part').open('x') as f:
            json.dump(state,f,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
        receipt.with_suffix('.part').replace(receipt)
    save();h=hashlib.sha256();size=0
    with archive.open('xb') as f:
        while chunk:=sys.stdin.buffer.read(1024**2):
            size+=len(chunk);assert size<=2*1024**2;h.update(chunk);f.write(chunk)
    assert h.hexdigest()==row['sha256']
    with tarfile.open(archive) as t:
        members=t.getmembers();assert all(Path(m.name).parts[0]=='nasm-3.02' for m in members)
        assert sum(m.size for m in members)<=32*1024**2
        t.extractall(source.parent,filter='data')
    assert 'SPDX-License-Identifier: BSD-2-Clause' in (source/'LICENSE').read_text()
    state['source_readability_metadata']=[]
    for name in ['Makefile.in','Mkfiles/msvc.mak','Mkfiles/openwcom.mak']:
        p=source/name;assert p.stat().st_mode&0o777==0o600
        digest=hashlib.sha256(p.read_bytes()).hexdigest()
        p.chmod(0o644)
        assert hashlib.sha256(p.read_bytes()).hexdigest()==digest
        state['source_readability_metadata'].append(dict(path=name,old_mode='0600',new_mode='0644',sha256=digest))
    work.mkdir();os.chown(work,101,101)
    for src,dst,ro in [(source,source_alias,True),(work,work_alias,False)]:
        dst.mkdir();state['pending_bind']=str(dst);save()
        subprocess.run(['mount','--bind',str(src),str(dst)],check=True)
        subprocess.run(['mount','-o','remount,bind,nosuid,nodev,'+('ro' if ro else 'rw'),str(dst)],check=True)
        assert dst.stat().st_ino==src.stat().st_ino
    state.pop('pending_bind');state.update(state='prepared',work=str(work_alias),source_alias=str(source_alias))
    save();print(json.dumps(state))


if __name__=='__main__':main()
