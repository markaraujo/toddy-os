"""Incremental same-source FUSE kernel build in the qualified private COW cache."""
from pathlib import Path
import hashlib,json,os,signal,subprocess,time
assert os.getuid()==os.getgid()==101
w=Path('/build');cache=w/'merged';result=w/'kernel-fuse-build-1'
assert not result.exists(),'Inspect actual configuration/job before any replay'
assert os.statvfs(w).f_bavail*os.statvfs(w).f_frsize>=300*1024**2
assert hashlib.sha256((cache/'.config').read_bytes()).hexdigest()=='5de998e9f70642f0061b147ba847e935a38ed45d4a30c77983fdabcb27f70656'
assert json.loads((w/'worker-isolation.json').read_text())['source_unchanged']
result.mkdir()
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def save(name,value):
 p=result/name;part=p.with_suffix('.part');part.write_text(json.dumps(value,indent=2)+'\n');part.replace(p)
def free():return os.statvfs(w).f_bavail*os.statvfs(w).f_frsize
def config(text):
 values={}
 for line in text.splitlines():
  if line.startswith('CONFIG_'):k,v=line.split('=',1);values[k]=v
  elif line.startswith('# CONFIG_') and line.endswith(' is not set'):values[line[2:-11]]='n'
 return values
old=(cache/'.config').read_text();(result/'before.config').write_text(old)
before_artifacts={name:sha(cache/name) for name in ['arch/x86/boot/bzImage','vmlinux','System.map','.config']}
save('intent.json',{'state':'configuring','before_artifacts':before_artifacts,'scope':'Same frozen Linux7.1.8 source/private incremental cache only, no install or boot acceptance'})
env=dict(os.environ,KBUILD_BUILD_USER='toddy',KBUILD_BUILD_HOST='builder',KBUILD_BUILD_VERSION='1',KBUILD_BUILD_TIMESTAMP='2026-11-05 00:00:00 UTC')
subprocess.run(['scripts/config','--module','FUSE_FS','--disable','CUSE','--disable','VIRTIO_FS','--disable','FUSE_PASSTHROUGH','--disable','FUSE_IO_URING'],cwd=cache,env=env,check=True)
subprocess.run(['make','RUSTC=false','olddefconfig'],cwd=cache,env=env,check=True)
before=config(old);after=config((cache/'.config').read_text());delta={k:[before.get(k,'n'),after.get(k,'n')] for k in before.keys()|after.keys() if before.get(k,'n')!=after.get(k,'n')}
assert delta.get('CONFIG_FUSE_FS')==['n','m']
assert set(delta)<={'CONFIG_FUSE_FS','CONFIG_FS_IOMAP'},delta
if 'CONFIG_FS_IOMAP' in delta:assert delta['CONFIG_FS_IOMAP']==['n','y']
assert after['CONFIG_SECURITY_LANDLOCK']=='y' and all(after.get(k,'n')=='n' for k in ['CONFIG_CUSE','CONFIG_VIRTIO_FS','CONFIG_FUSE_PASSTHROUGH','CONFIG_FUSE_IO_URING'])
save('config-delta.json',delta);(result/'resolved.config').write_bytes((cache/'.config').read_bytes())
assert subprocess.check_output(['make','RUSTC=false','-s','kernelrelease'],cwd=cache,env=env,text=True).strip()=='7.1.8-toddy'
started=time.monotonic();minimum=free();last=0;reason=None
with (result/'make.log').open('xb') as log:
 p=subprocess.Popen(['make','RUSTC=false','-j4','bzImage','modules'],cwd=cache,env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
 save('process.json',{'pid':p.pid,'start_ticks':Path('/proc/'+str(p.pid)+'/stat').read_text().rsplit(')',1)[1].split()[19],'command':['make','RUSTC=false','-j4','bzImage','modules']})
 while p.poll() is None:
  available=free();minimum=min(minimum,available)
  if available<128*1024**2 and reason is None:reason='128MiB scratch reserve reached';os.killpg(p.pid,signal.SIGINT)
  if time.monotonic()-last>=10:save('progress.json',{'elapsed_seconds':round(time.monotonic()-started,1),'free_bytes':available,'minimum_free_bytes':minimum,'log_bytes':(result/'make.log').stat().st_size,'compiler_live':p.poll() is None,'stop_reason':reason});last=time.monotonic()
  time.sleep(1)
 code=p.wait()
save('compile-result.json',{'exit':code,'elapsed_seconds':round(time.monotonic()-started,3),'minimum_free_bytes':minimum,'stop_reason':reason,'final_free_bytes':free()})
assert code==0 and reason is None and free()>=128*1024**2
baseline=json.loads((w/'baseline.json').read_text())
for name,row in baseline['pristine_source'].items():
 for root in [Path('/src/cache'),cache]:
  p=root/name
  if 'sha256' in row:assert sha(p)==row['sha256'],str(p)
  else:assert os.readlink(p)==row['link'],str(p)
save('source-verified.json',{'pristine_source_entries':len(baseline['pristine_source']),'private_and_original_source_unchanged':True})
oldmodules=json.loads((w/'kernel-stage-1.json').read_text())['modules']
for name,digest in oldmodules.items():assert sha(cache/name)==digest,name
new=['fs/fuse/fuse.ko'];ordered={n.removesuffix('.o')+'.ko' for n in (cache/'modules.order').read_text().splitlines()}
assert ordered==set(oldmodules)|set(new),ordered-set(oldmodules)
artifacts={name:sha(cache/name) for name in ['arch/x86/boot/bzImage','vmlinux','System.map','.config',*new]}
save('artifacts.json',artifacts);save('verified-result.json',{'compile_exit':0,'config_delta':delta,'original_modules_unchanged':len(oldmodules),'new_modules':new,'source_entries_verified':len(baseline['pristine_source']),'artifacts':artifacts,'scope':'Private cached compiler output only; candidate module/kernel native boot and privileged FUSE tests still required'})
print(json.dumps({'compile_exit':0,'config_delta':delta,'original_modules_unchanged':len(oldmodules),'artifacts':artifacts}))
