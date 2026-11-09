#!/usr/bin/env python3
"""Keep every frozen artifact path/byte, sharing verified identical inode content."""
import hashlib
import fcntl
import json
import os
from pathlib import Path
import shutil
import stat

ROOT=Path(__file__).resolve().parents[2]


def digest(path):
    with path.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()


def main():
    receipt=ROOT/'.local/phase2/release-artifact-copy-custody.json'
    lock=open(receipt.with_suffix('.lock'),'a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    assert not receipt.exists(),'Inspect previous custody and actual paths; never replay'
    assert shutil.disk_usage(ROOT).free>=100*1024**3
    folders=['releases/toddy-foundation-2026-11-07','releases/foundation-2026-11-07',
             'release-staging/v0.1.0-foundation.1','release-staging/download-audit','release-staging/licensed-download-audit']
    rows=[];seen={}
    for folder in folders:
        for name in ['toddy-foundation-x86_64.iso','source-archives.tar']:
            path=ROOT/'.local'/folder/name;s=path.lstat()
            assert path.resolve()==path and stat.S_ISREG(s.st_mode) and s.st_uid==os.getuid()
            assert s.st_dev==ROOT.stat().st_dev and stat.S_IMODE(s.st_mode)&0o444==0o444
            assert not os.listxattr(path,follow_symlinks=False) and s.st_size>64*1024**2
            identity=(s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns)
            if identity not in seen:seen[identity]=digest(path)
            rows.append({'path':str(path.relative_to(ROOT)),'device':s.st_dev,'inode':s.st_ino,'bytes':s.st_size,
                         'mtime_ns':s.st_mtime_ns,'mode':stat.S_IMODE(s.st_mode),'uid':s.st_uid,'gid':s.st_gid,
                         'allocated_bytes':s.st_blocks*512,'sha256':seen[identity]})
    groups={}
    for r in rows:groups.setdefault((r['sha256'],r['bytes'],r['device'],r['uid'],r['gid']),[]).append(r)
    record={'scope':'Only frozen local release ISO/upstream-source archive copies; every pathname/content/checksum retained, no VM disk or published remote artifact changed',
            'state':'verified','before_free_bytes':shutil.disk_usage(ROOT).free,'files':rows,
            'controller_pid':os.getpid(),'controller_boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip(),
            'controller_start_ticks':Path('/proc/self/stat').read_text().split()[21],
            'artifact_mode':'Verified immutable artifact groups normalized to read-only0444; old per-path metadata retained here',
            'recovery':'Content remains at every original path. To restore independent ownership/mode/timestamp metadata, copy verified canonical bytes to a new temporary file, apply recorded metadata and atomically replace only that alias; never edit shared immutable artifacts in place.'}
    def save():
        part=receipt.with_suffix('.part');assert not part.exists()
        with part.open('x') as f:f.write(json.dumps(record,indent=2)+'\n');f.flush();os.fsync(f.fileno())
        part.replace(receipt)
    save()
    for group in groups.values():
        if len({r['inode'] for r in group})<2:continue
        canonical=ROOT/group[0]['path'];record['state']='sharing-verified-identical-content';save()
        for row in group:
            path=ROOT/row['path'];s=path.lstat()
            assert (s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns)==(row['device'],row['inode'],row['bytes'],row['mtime_ns'])
        canonical.chmod(0o444)
        for row in group:
            path=ROOT/row['path']
            if path.stat().st_ino!=canonical.stat().st_ino:
                part=path.with_name(path.name+'.toddy-link.part');assert not part.exists()
                os.link(canonical,part);os.replace(part,path)
                directory=os.open(path.parent,os.O_RDONLY|os.O_DIRECTORY)
                try:os.fsync(directory)
                finally:os.close(directory)
            row['shared_inode']=path.stat().st_ino;save()
        assert digest(canonical)==group[0]['sha256']
        assert all((ROOT/r['path']).stat().st_ino==canonical.stat().st_ino for r in group)
    before={r['inode']:r['allocated_bytes'] for r in rows};after={}
    for r in rows:
        p=ROOT/r['path'];s=p.stat();assert s.st_size==r['bytes']
        assert digest(p)==r['sha256'];after[s.st_ino]=s.st_blocks*512
    record.update(state='complete',allocation_reclaimed_bytes=sum(before.values())-sum(after.values()),
                  after_free_bytes=shutil.disk_usage(ROOT).free)
    save();print(json.dumps({k:record[k] for k in ['state','allocation_reclaimed_bytes','before_free_bytes','after_free_bytes']}))


if __name__=='__main__':main()
