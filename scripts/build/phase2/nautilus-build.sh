#!/bin/bash
set -euo pipefail
[[ $(id -u) == 101 && ! -e /build/compile ]]
export PYTHONDONTWRITEBYTECODE=1
ulimit -c 0
# Frozen BLFS13.1-systemd gnome/nautilus.html, SHA256
# a68a45f372ce35ddc351ea1769e2c84ce2709719502ea4aa1121b0e1563da5f8.
# Actual50.2.2 feature options use disabled; compile all original test programs.
meson setup /build/compile /src --prefix=/usr --libdir=lib --buildtype=release \
    --wrap-mode=nofallback -Dselinux=disabled -Dcloudproviders=disabled \
    -Ddocs=false -Dextensions=true -Dintrospection=true -Dtests=all \
    > /build/configure.log 2>&1
python3 - <<'PY'
from pathlib import Path
import hashlib,json,os,signal,subprocess,time
work=Path('/build');floor=128*1024**2;margin=32*1024**2
resources=[]
def available():
 s=os.statvfs(work);return s.f_bavail*s.f_frsize
for name,command in [('compile',['ninja','-C','/build/compile','-j6']),('stage',['meson','install','-C','/build/compile','--no-rebuild','--destdir=/stage'])]:
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
 row={'phase':name,'command':command,'exit':exit_code,'elapsed_seconds':round(time.monotonic()-started,3),'initial_free':initial,'minimum_free':minimum,'final_free':final,'reserve':floor,'stop_margin':margin,'interrupted_for_reserve':stopped}
 resources.append(row);(work/'resources.json').write_text(json.dumps(resources,indent=2)+'\n')
 assert exit_code==0 and not stopped and final>=floor,row
inventory=subprocess.check_output(['meson','introspect','/build/compile','--tests'],text=True)
tests=json.loads(inventory);assert tests
(work/'original-test-inventory.json').write_text(inventory)
artifacts={}
for p in (work/'compile').rglob('*'):
 if p.is_file() and not p.is_symlink():
  with p.open('rb') as f:
   if f.read(4)!=b'\x7fELF':continue
   f.seek(0);artifacts[str(p.relative_to(work/'compile'))]=hashlib.file_digest(f,'sha256').hexdigest()
stage={str(p.relative_to('/stage')):hashlib.sha256(p.read_bytes()).hexdigest() for p in Path('/stage').rglob('*') if p.is_file() and not p.is_symlink()}
assert 'src/nautilus' in artifacts and 'usr/bin/nautilus' in stage
code_sections={}
for section in ['.text','.rodata']:
 compiled=subprocess.check_output(['readelf','-x',section,str(work/'compile/src/nautilus')])
 installed=subprocess.check_output(['readelf','-x',section,'/stage/usr/bin/nautilus'])
 assert compiled==installed,'Unexpected installed executable code/constant change'
 code_sections[section]=hashlib.sha256(compiled).hexdigest()
result={'scope':'Pinned Nautilus50.2.2 isolated release compiler/stage and full original test inventory only. No original tests executed: graphical native user-seat gate remains required. No native install/CLI/GUI/file operation acceptance. Optional cloudproviders/SELinux UI disabled using supported frozen-book options; extensions/introspection/all original test programs retained.','compile_exit':0,'stage_exit':0,'installed_code_sections_unchanged':code_sections,'resources':resources,'artifacts':artifacts,'stage_sha256':stage,'registered_test_count':len(tests),'original_tests_executed':False}
(work/'stage-results.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'compile_exit':0,'stage_exit':0,'ELFs':len(artifacts),'stage_regular_files':len(stage),'registered_tests':len(tests),'native_graphical_tests_pending':True}))
PY
