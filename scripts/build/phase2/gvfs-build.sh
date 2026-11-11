#!/bin/bash
set -euo pipefail
[[ $(id -u) == 101 && ! -e /build/compile ]]
export PYTHONDONTWRITEBYTECODE=1
ulimit -c 0
# Frozen BLFS13.1-systemd gnome/gvfs.html, SHA256
# ecff8579f8b9e31680b4de9b49e049ae020a64a3c7fbc409b4e3f4c4026e445c.
# Keep existing owned SMB/archive/HTTP/SFTP/UDisks/admin backends. Optional
# camera/mobile/optical/discovery/cloud dependencies are absent or unqualified.
meson setup /build/compile /src --prefix=/usr --libdir=lib --libexecdir=libexec \
    --buildtype=release --wrap-mode=nofallback -Dunit_tests=true \
    -Donedrive=false -Dfuse=false -Dgphoto2=false -Dafc=false -Dbluray=false \
    -Dnfs=false -Dmtp=false -Ddnssd=false -Dgoa=false -Dcdda=false -Dwsdd=false \
    > /build/configure.log 2>&1
python3 - <<'PY'
from pathlib import Path
import hashlib,json,os,re,signal,subprocess,time
work=Path('/build');floor=128*1024**2;margin=32*1024**2;resources=[]
def available():
 s=os.statvfs(work);return s.f_bavail*s.f_frsize
for name,command in [('compile',['ninja','-C','/build/compile','-j4']),('stage',['meson','install','-C','/build/compile','--no-rebuild','--destdir=/stage'])]:
 initial=available();assert initial>=floor+margin
 minimum=initial;stopped=False;started=time.monotonic()
 with (work/(name+'.log')).open('xb') as output:
  process=subprocess.Popen(command,stdout=output,stderr=subprocess.STDOUT,start_new_session=True)
  while process.poll() is None:
   free=available();minimum=min(minimum,free)
   if free<floor+margin:
    stopped=True;os.killpg(process.pid,signal.SIGTERM)
    try:process.wait(timeout=10)
    except subprocess.TimeoutExpired:os.killpg(process.pid,signal.SIGKILL);process.wait(timeout=10)
    break
   time.sleep(.25)
  exit_code=process.wait()
 final=available();minimum=min(minimum,final)
 resources.append({'phase':name,'exit':exit_code,'elapsed_seconds':round(time.monotonic()-started,3),'initial_free':initial,'minimum_free':minimum,'final_free':final,'reserve':floor,'interrupted_for_reserve':stopped})
 (work/'resources.json').write_text(json.dumps(resources,indent=2)+'\n')
 assert exit_code==0 and not stopped and final>=floor,resources[-1]
artifacts={}
for p in (work/'compile').rglob('*'):
 if p.is_file() and not p.is_symlink() and p.open('rb').read(4)==b'\x7fELF':
  with p.open('rb') as f:artifacts[str(p.relative_to(work/'compile'))]=hashlib.file_digest(f,'sha256').hexdigest()
# Original outputstream driver accepts a test URI. This exercises only its
# local file backend; remote/admin/trash require separate native runtime proof.
directory=work/'outputstream-data';directory.mkdir()
r=subprocess.run([str(work/'compile/test/unit/outputstream'),str(directory)],capture_output=True,text=True,timeout=45)
(work/'outputstream.stdout').write_text(r.stdout);(work/'outputstream.stderr').write_text(r.stderr)
assert r.returncode==0,(r.returncode,r.stderr)
plans=re.findall(r'^1\.\.(\d+)\s*$',r.stdout,re.M);assert len(plans)==1
passed=re.findall(r'^ok\s+\d+\s+([^\n]+)',r.stdout,re.M)
assert len(passed)==int(plans[0]) and not re.search(r'(?im)\b(?:SKIP|TODO)\b|^not ok',r.stdout)
for name,sha in artifacts.items():assert hashlib.sha256((work/'compile'/name).read_bytes()).hexdigest()==sha
stage={str(p.relative_to('/stage')):hashlib.sha256(p.read_bytes()).hexdigest() for p in Path('/stage').rglob('*') if p.is_file() and not p.is_symlink()}
assert 'usr/libexec/gvfsd' in stage and 'usr/libexec/gvfsd-trash' in stage
result={'scope':'Frozen Gvfs1.60.2 isolated release compile/stage and original outputstream local-file cases only; no installed trash/admin/network/backend or GUI acceptance.', 'compile_exit':0,'stage_exit':0,'original_outputstream':{'exit':r.returncode,'cases':len(passed),'skipped':0},'resources':resources,'artifacts':artifacts,'stage_sha256':stage}
(work/'stage-results.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'compile_exit':0,'stage_exit':0,'local_outputstream_cases':len(passed),'ELFs':len(artifacts),'stage_regular_files':len(stage)}))
PY
