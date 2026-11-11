#!/usr/bin/env python3
"""Reconcile completed guest growth and retained host preallocation, no resize replay."""
from pathlib import Path
import hashlib,json,os,shlex,shutil,stat,subprocess
import phase2_vm as vm

def main():
 p=vm.WORK/'kernel-fuse-growth.json';row=json.loads(p.read_text());assert row['state'] in ['qmp-grown-filesystem-pending','filesystem-grown','filesystem-grown-allocation-pending']
 assert row.get('allocation_reconciled') is not True,'Inspect already completed postconditions; do not repeat'
 code="from pathlib import Path;print(Path('/var/log/toddy/phase2/kernel-fuse-resize-1.json').read_text(),end='')"
 data=subprocess.check_output(vm.ssh_args()+['python3 -c '+shlex.quote(code)]);guest=json.loads(data)
 assert guest['state']=='filesystem-grown' and guest['uuid']==row['filesystem_uuid']=='c6c4176d-faed-4ee3-9ae0-94914a0af666' and guest['new_bytes']==row['new_bytes']==2*1024**3 and guest['baseline_and_config_unchanged']
 disk=vm.WORK/'kernel-landlock-scratch.raw';assert not disk.is_symlink();st=disk.stat()
 assert stat.S_ISREG(st.st_mode) and st.st_size==row['new_bytes'] and st.st_ino==row['inode'] and st.st_dev==row['device'] and st.st_uid==os.getuid() and st.st_nlink==1 and not st.st_mode&0o077
 missing=max(0,st.st_size-st.st_blocks*512);assert shutil.disk_usage(disk.parent).free-missing>=100*1024**3
 def save():
  part=p.with_suffix('.part');assert not part.exists();part.write_text(json.dumps(row,indent=2)+'\n');part.chmod(0o600);part.replace(p)
 row.update(state='filesystem-grown-allocation-pending',allocated_after_guest_resize=st.st_blocks*512,guest_receipt_sha256=hashlib.sha256(data).hexdigest(),guest_result=guest);save()
 # QMP resize/guest geometry update may release a small physical extent. This
 # allocates holes at the EXISTING logical size, preserves bytes, and never
 # repeats QMP block_resize or resize2fs or changes the filesystem geometry.
 subprocess.run(['fallocate','-l',str(st.st_size),str(disk)],check=True)
 actual=disk.stat();assert actual.st_ino==st.st_ino and actual.st_dev==st.st_dev and actual.st_size==st.st_size and actual.st_blocks*512>=actual.st_size
 assert shutil.disk_usage(disk.parent).free>=100*1024**3
 row.update(state='filesystem-grown',allocation_reconciled=True,allocated_bytes=actual.st_blocks*512,host_free_after=shutil.disk_usage(disk.parent).free);save();vm.kernel_scratch_arguments();print(json.dumps(row))
if __name__=='__main__':main()
