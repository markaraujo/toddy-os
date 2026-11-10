#!/usr/bin/env python3
"""Reserve one bounded virtual build file; no guest attachment or formatting."""
from pathlib import Path
import json,os,shutil,subprocess
import phase2_vm

def main():
 root=phase2_vm.ROOT;work=phase2_vm.WORK
 receipt=work/'kernel-landlock-scratch.json';pending=work/'kernel-landlock-scratch.pending.json';disk=work/'kernel-landlock-scratch.raw'
 assert work.resolve()==work and not any(p.exists() or p.is_symlink() for p in [receipt,pending,disk]),'Reconcile preparation; never replay'
 size=phase2_vm.KERNEL_SCRATCH_BYTES;reserve=100*1024**3;before=shutil.disk_usage(root).free
 assert before>=reserve+size+128*1024**2,'Host reserve and allocation headroom required'
 row={'state':'preparing','scope':'Dedicated bounded virtual kernel cache COW scratch only. No physical disk or target installation; not attached/formatted here.','filename':disk.name,'format':'raw','bytes':size,'serial':'TODDY-B02-KERNEL','host_free_before':before,'host_minimum_reserve_bytes':reserve,'discard':'ignore; retain preallocated host allocation'}
 def save():
  with pending.open('w') as f:json.dump(row,f,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
 save()
 fd=os.open(disk,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600);os.close(fd)
 subprocess.run(['fallocate','-l',str(size),str(disk)],check=True)
 with disk.open('rb') as f:
  assert f.read(4096)==bytes(4096);f.seek(size-4096);assert f.read(4096)==bytes(4096)
 s=disk.stat();assert s.st_size==size and s.st_blocks*512>=size and s.st_nlink==1
 after=shutil.disk_usage(root).free;assert after>=reserve
 row.update(state='prepared',device=s.st_dev,inode=s.st_ino,allocated_bytes=s.st_blocks*512,host_free_after=after);save();pending.rename(receipt)
 assert phase2_vm.kernel_scratch_arguments();print(json.dumps(row))
if __name__=='__main__':main()
