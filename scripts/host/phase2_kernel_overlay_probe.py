#!/usr/bin/env python3
"""Qualify metadata-only COW on disposable data before reusing a kernel cache."""
from pathlib import Path
import shlex,subprocess
import phase2_vm

def main():
 code=r'''from pathlib import Path
import errno,fcntl,hashlib,json,os,subprocess
subprocess.run(['bash','-c','source /opt/toddy-build/scripts/build/target.sh; guard_target'],check=True)
lock=open('/var/log/toddy/build/build.lock','a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
assert not list(Path('/var/log/toddy/build').glob('*.running.json'))
l=Path('/var/log/toddy/phase2');receipt=l/'kernel-overlay-test-1.json';source=Path('/mnt/lfs/sources/phase2/inputs/kernel-overlay-test-1');work=Path('/mnt/lfs/sources/phase2/work/kernel-overlay-test-1')
assert not receipt.exists() and not source.exists() and not work.exists(),'Reconcile prior state; never replay'
fs=os.statvfs('/mnt/lfs');assert fs.f_bavail*fs.f_frsize>=16*1024**3+16*1024**2
source.mkdir();lower=source/'lower';lower.mkdir();(lower/'probe.bin').write_bytes(b'K'*4*1024**2);os.chmod(lower/'probe.bin',0o644)
work.mkdir();os.chown(work,101,101)
for name in ['upper','overlay-work','merged']:(work/name).mkdir()
before=hashlib.sha256((lower/'probe.bin').read_bytes()).hexdigest()
state={'state':'prepared','scope':'Disposable synthetic4MiB overlay/metacopy/UID101/readonly-input denial qualification only; no real kernel or guest package change','lower_sha256':before,'lower_uid':0};receipt.write_text(json.dumps(state,indent=2)+'\n')
options=f'lowerdir={lower},upperdir={work}/upper,workdir={work}/overlay-work,metacopy=on,index=off'
subprocess.run(['mount','-t','overlay','overlay','-o',options,str(work/'merged')],check=True)
state['state']='mounted';receipt.write_text(json.dumps(state,indent=2)+'\n')
try:
 os.chown(work/'merged',101,101);os.chown(work/'merged/probe.bin',101,101)
 upper=work/'upper/probe.bin';assert upper.stat().st_size==4*1024**2 and upper.stat().st_blocks<=8
 assert 'trusted.overlay.metacopy' in os.listxattr(upper)
 fd=os.open(upper,os.O_RDONLY)
 try:
  try:os.lseek(fd,0,os.SEEK_DATA)
  except OSError as error:assert error.errno==errno.ENXIO
  else:raise AssertionError('Metacopy unexpectedly has file data extents')
 finally:os.close(fd)
 state['metadata_only_blocks_before_write']=upper.stat().st_blocks
 lock.close()
 probe="""from pathlib import Path
import hashlib,json,os
assert os.geteuid()==101
s=Path('/proc/self/status').read_text();assert 'NoNewPrivs:\\t1' in s and 'CapEff:\\t0000000000000000' in s
assert Path('/build/merged/probe.bin').stat().st_uid==101
for name in ['/src/lower/probe.bin','/usr/.toddy-cow-denial']:
 try:Path(name).write_bytes(b'FORBIDDEN')
 except PermissionError:pass
 except OSError as e:assert e.errno==30
 else:raise AssertionError('Outside private writable output accepted')
assert not Path('/var/lib/dpkg/status').exists()
Path('/build/merged/probe.bin').write_bytes(b'private upper payload\\n')
assert Path('/src/lower/probe.bin').read_bytes()==b'K'*4*1024**2
print(json.dumps({'uid':os.geteuid(),'readonly_inputs_denied':True,'private_overlay_write':True,'package_database_absent':True}))
"""
 with (l/'kernel-overlay-test-1.log').open('xb') as output:r=subprocess.run(['bash','/opt/toddy-build/scripts/build/phase2/isolated.sh',str(source),str(work),'python3','-c',probe],stdout=output,stderr=subprocess.STDOUT)
 assert r.returncode==0,(l/'kernel-overlay-test-1.log').read_text()
 assert hashlib.sha256((lower/'probe.bin').read_bytes()).hexdigest()==before and (lower/'probe.bin').stat().st_uid==0 and (lower/'probe.bin').stat().st_mode&0o777==0o644
 assert (work/'merged/probe.bin').read_bytes()==b'private upper payload\n'
 state.update(state='qualified',actual_unprivileged_namespace_exit=0,lower_content_owner_mode_unchanged=True,metadata_only_before_write=True)
finally:
 subprocess.run(['umount',str(work/'merged')],check=True)
receipt.write_text(json.dumps(state,indent=2)+'\n');print(json.dumps(state))
'''
 result=subprocess.run(phase2_vm.ssh_args()+['python3 -c '+shlex.quote(code)],capture_output=True,text=True)
 prefix=Path('.local/phase2/kernel-overlay-test-1-controller');assert not prefix.with_suffix('.log').exists();prefix.with_suffix('.log').write_text(result.stdout+result.stderr);prefix.with_suffix('.exit').write_text(str(result.returncode)+'\n');print(result.stdout,result.stderr);raise SystemExit(result.returncode)
if __name__=='__main__':main()
