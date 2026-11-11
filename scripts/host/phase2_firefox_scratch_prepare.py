#!/usr/bin/env python3
"""Preallocate one explicitly bounded browser build file, without formatting."""
from pathlib import Path
import fcntl,json,os,shutil
import phase2_vm


def main():
    work=phase2_vm.WORK
    assert os.geteuid()!=0 and work.resolve()==work and not work.is_symlink()
    lock=open(work/'firefox-scratch-prepare.lock','a')
    fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    receipt=work/'firefox-scratch.json';pending=work/'firefox-scratch.pending.json'
    disk=work/'firefox-scratch.raw'
    assert not any(p.exists() or p.is_symlink() for p in [receipt,pending,disk]),'Inspect actual allocation; never replay'
    size=phase2_vm.FIREFOX_SCRATCH_BYTES;reserve=100*1024**3
    before=shutil.disk_usage(work).free
    assert before>=reserve+size+512*1024**2,'Full allocation plus real reserve/headroom required'
    row={'state':'preparing','scope':'New dedicated browser compiler/source/stage file only; not a host disk, installer target or foundation replacement. No guest attachment/format here.',
         'filename':disk.name,'format':'raw','bytes':size,'serial':'TODDY-B02-FIREFOX',
         'host_free_before':before,'host_minimum_reserve_bytes':reserve,'discard':'ignore; retain full host allocation'}
    def save():
        with pending.open('w') as f:
            os.fchmod(f.fileno(),0o600);json.dump(row,f,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
    save()
    fd=os.open(disk,os.O_RDWR|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
    try:
        original=os.fstat(fd);row.update(device=original.st_dev,inode=original.st_ino);save()
        os.posix_fallocate(fd,0,size);os.fsync(fd)
        actual=os.fstat(fd)
        assert actual.st_ino==original.st_ino and actual.st_size==size and actual.st_blocks*512>=size
        assert actual.st_nlink==1 and actual.st_uid==os.getuid()
        assert os.pread(fd,4096,0)==bytes(4096) and os.pread(fd,4096,size-4096)==bytes(4096)
    finally:os.close(fd)
    after=shutil.disk_usage(work).free;assert after>=reserve+128*1024**2
    row.update(state='prepared',allocated_bytes=actual.st_blocks*512,host_free_after=after);save()
    pending.rename(receipt)
    d=os.open(work,os.O_RDONLY|os.O_DIRECTORY)
    try:os.fsync(d)
    finally:os.close(d)
    assert phase2_vm.firefox_scratch_arguments();print(json.dumps(row))


if __name__=='__main__':main()
