"""Affected same-source kernel feature build in the qualified private cache only."""
from pathlib import Path
import hashlib,json,os,signal,stat,subprocess,time
assert os.getuid()==101
w=Path('/build');cache=w/'merged';result=w/'kernel-build-1';assert not result.exists();result.mkdir()
assert json.loads((w/'worker-isolation.json').read_text())['source_unchanged']
baseline=json.loads((w/'baseline.json').read_text())
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def save(name,value):
 p=result/name;part=p.with_suffix('.part');part.write_text(json.dumps(value,indent=2)+'\n');part.replace(p)
def free():return os.statvfs(w).f_bavail*os.statvfs(w).f_frsize
old=(cache/'.config').read_text();assert old==Path('/src/cache/.config').read_text()
assert old.count('# CONFIG_SECURITY_LANDLOCK is not set')==1
(result/'before.config').write_text(old)
(cache/'.config').write_text(old.replace('# CONFIG_SECURITY_LANDLOCK is not set','CONFIG_SECURITY_LANDLOCK=y'))
env=dict(os.environ,KBUILD_BUILD_USER='toddy',KBUILD_BUILD_HOST='builder',KBUILD_BUILD_VERSION='1',KBUILD_BUILD_TIMESTAMP='2026-11-05 00:00:00 UTC')
subprocess.run(['make','RUSTC=false','olddefconfig'],cwd=cache,env=env,check=True)
def config(text):
 values={}
 for line in text.splitlines():
  if line.startswith('CONFIG_'):key,value=line.split('=',1);values[key]=value
  elif line.startswith('# CONFIG_') and line.endswith(' is not set'):values[line[2:-11]]='n'
 return values
before=config(old);after=config((cache/'.config').read_text());delta={k:[before.get(k),after.get(k)] for k in before.keys()|after.keys() if before.get(k)!=after.get(k)}
assert delta=={'CONFIG_SECURITY_LANDLOCK':['n','y'],'CONFIG_SECURITY_PATH':['n','y']},delta
save('config-delta.json',delta);(result/'resolved.config').write_bytes((cache/'.config').read_bytes())
assert subprocess.check_output(['make','RUSTC=false','-s','kernelrelease'],cwd=cache,env=env,text=True).strip()=='7.1.8-toddy'
started=time.monotonic();minimum=free();last=0;reason=None
with (result/'make.log').open('xb') as log:
 p=subprocess.Popen(['make','RUSTC=false','-j4','bzImage','modules'],cwd=cache,env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
 save('process.json',{'pid':p.pid,'command':['make','RUSTC=false','-j4','bzImage','modules'],'start_ticks':Path('/proc/'+str(p.pid)+'/stat').read_text().split()[21]})
 while p.poll() is None:
  available=free();minimum=min(minimum,available)
  if available<128*1024**2 and reason is None:
   reason='128MiB scratch reserve reached; compiler-only safe SIGINT';os.killpg(p.pid,signal.SIGINT)
  if time.monotonic()-last>=10:
   save('progress.json',{'elapsed_seconds':round(time.monotonic()-started,1),'free_bytes':available,'minimum_free_bytes':minimum,'log_bytes':(result/'make.log').stat().st_size,'compiler_live':p.poll() is None,'stop_reason':reason});last=time.monotonic()
  time.sleep(1)
 code=p.wait()
minimum=min(minimum,free())
save('compile-result.json',{'exit':code,'elapsed_seconds':round(time.monotonic()-started,3),'minimum_free_bytes':minimum,'stop_reason':reason,'final_free_bytes':free(),'scratch_reserve_met_after_compile':free()>=128*1024**2})
assert code==0 and reason is None
# Kernel source itself must retain frozen bytes in both original and private view.
for name,row in baseline['pristine_source'].items():
 for root in [Path('/src/cache'),cache]:
  p=root/name
  if 'sha256' in row:assert sha(p)==row['sha256'],str(p)
  else:assert os.readlink(p)==row['link'],str(p)
assert Path('/src/cache/.config').read_text()==old
save('source-verified.json',{'pristine_source_entries':len(baseline['pristine_source']),'private_and_original_source_unchanged':True,'original_config_unchanged':True})
artifacts={name:sha(cache/name) for name in ['arch/x86/boot/bzImage','vmlinux','System.map','.config']};save('artifacts.json',artifacts)
print(json.dumps({'compile_exit':0,'config_delta':delta,'elapsed_seconds':round(time.monotonic()-started,3),'minimum_free_bytes':minimum,'artifacts':artifacts,'pristine_source_entries':len(baseline['pristine_source'])}))
