#!/usr/bin/env python3
"""One bounded 1GiB growth for FUSE compilation of the existing fixed virtual build scratch only."""
from pathlib import Path
import hashlib,json,os,shlex,shutil,socket,stat,subprocess
import phase2_vm as vm
OLD=1024**3;NEW=2*1024**3

def main():
 disk=vm.WORK/'kernel-landlock-scratch.raw';receipt=vm.WORK/'kernel-fuse-growth.json'
 assert not receipt.exists() and not receipt.with_suffix('.part').exists(),'Reconcile actual size/QMP/guest receipt; never repeat uncertain growth'
 vm.kernel_scratch_arguments();st=disk.stat();assert st.st_size==OLD
 reserve=100*1024**3;assert shutil.disk_usage(disk.parent).free-(NEW-OLD)>=reserve
 before='''from pathlib import Path
import fcntl,json,subprocess
p=Path('/var/log/toddy/phase2');lock=open('/var/log/toddy/build/build.lock','a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
assert not list(Path('/var/log/toddy/build').glob('*.running.json'))
assert (p/'kernel-fuse-build-1.exit').read_text().strip()=='1'
r=json.loads(Path('/mnt/lfs/sources/phase2/work/kernel-landlock-1/kernel-fuse-build-1/compile-result.json').read_text());assert r['exit']==-2 and r['stop_reason'].startswith('128MiB')
print(json.dumps(r))
'''
 verified=json.loads(subprocess.check_output(vm.ssh_args()+['python3 -c '+shlex.quote(before)],text=True))
 sock=socket.socket(socket.AF_UNIX,socket.SOCK_STREAM);sock.settimeout(15);sock.connect(str(vm.WORK/'qmp.sock'));f=sock.makefile('rwb');greeting=json.loads(f.readline());sequence=0
 def q(command,arguments=None):
  nonlocal sequence
  sequence+=1;msg={'execute':command,'id':sequence}
  if arguments is not None:msg['arguments']=arguments
  f.write((json.dumps(msg)+'\n').encode());f.flush()
  while True:
   out=json.loads(f.readline())
   if out.get('id')==sequence:
    assert 'error' not in out,out;return out['return']
 q('qmp_capabilities');block=next(x for x in q('query-block') if x['device']=='b02kernel');image=block['inserted']['image']
 assert image['virtual-size']==OLD and image['format']=='raw' and image['filename']=='/vm/phase2/kernel-landlock-scratch.raw'
 result={'state':'growth-intended','scope':'Fixed preallocated virtual scratch only, no physical disk/target root resize','serial':'TODDY-B02-KERNEL','old_bytes':OLD,'new_bytes':NEW,'growth_bytes':NEW-OLD,'device':st.st_dev,'inode':st.st_ino,'original_receipt_sha256':hashlib.sha256((vm.WORK/'kernel-landlock-scratch.json').read_bytes()).hexdigest(),'previous_growth_sha256':hashlib.sha256((vm.WORK/'kernel-landlock-growth.json').read_bytes()).hexdigest(),'filesystem_uuid':'c6c4176d-faed-4ee3-9ae0-94914a0af666','host_reserve_bytes':reserve,'host_free_before':shutil.disk_usage(disk.parent).free,'stopped_compiler':verified,'qmp_version':greeting['QMP']['version']}
 def save():
  part=receipt.with_suffix('.part')
  with part.open('x') as stream:os.fchmod(stream.fileno(),0o600);stream.write(json.dumps(result,indent=2)+'\n');stream.flush();os.fsync(stream.fileno())
  part.replace(receipt)
 save();subprocess.run(['fallocate','-l',str(NEW),str(disk)],check=True)
 ds=disk.stat();assert ds.st_dev==st.st_dev and ds.st_ino==st.st_ino and ds.st_size==NEW and ds.st_blocks*512>=NEW
 assert shutil.disk_usage(disk.parent).free>=reserve
 result.update(state='host-extension-preallocated',allocated_bytes=ds.st_blocks*512,host_free_after=shutil.disk_usage(disk.parent).free);save()
 q('block_resize',{'device':'b02kernel','size':NEW});actual=next(x for x in q('query-block') if x['device']=='b02kernel');assert actual['inserted']['image']['virtual-size']==NEW
 result.update(state='qmp-grown-filesystem-pending');save();print(json.dumps(result))
if __name__=='__main__':main()
