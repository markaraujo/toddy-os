#!/bin/bash
set -euo pipefail
[[ $(id -u) == 101 && ! -e /build/compile ]]
export PYTHONDONTWRITEBYTECODE=1
ulimit -c 0
[[ $(pkg-config --modversion tinysparql-3.0) == 3.11.1 ]]
mkdir -m700 /build/runtime
export XDG_RUNTIME_DIR=/build/runtime GSETTINGS_BACKEND=memory
# Explicit Landlock is upstream's distribution-build path. Runtime sandbox
# acceptance remains a separate native-kernel gate, never inferred from headers.
meson setup /build/compile /src --prefix=/usr --libdir=lib --libexecdir=libexec --sysconfdir=/etc --buildtype=release --wrap-mode=nofallback -Ddebug=false -Dman=false -Dextract=true -Dminer_fs=true -Dwriteback=true -Dseccomp=true -Dlandlock=enabled -Dfunctional_tests=true -Dsandbox_tests=true -Dbattery_detection=upower -Dcharset_detection=icu -Dsystemd_user_services=true
python3 - <<'PY'
from pathlib import Path
import json,os,signal,subprocess,time
floor=16*1024**3;stop_margin=16*1024**2
s=os.statvfs('/build');initial=s.f_bavail*s.f_frsize
assert initial>floor+stop_margin
p=subprocess.Popen(['ninja','-C','/build/compile','-j4'],start_new_session=True)
minimum=initial;interrupted=False
while p.poll() is None:
 s=os.statvfs('/build');free=s.f_bavail*s.f_frsize;minimum=min(minimum,free)
 if free<floor+stop_margin and not interrupted:
  os.killpg(p.pid,signal.SIGINT);interrupted=True
 time.sleep(0.25)
s=os.statvfs('/build');final=s.f_bavail*s.f_frsize;minimum=min(minimum,final)
Path('/build/compile-resource.json').write_text(json.dumps({'exit':p.returncode,'initial_free':initial,'minimum_free':minimum,'final_free':final,'reserve':floor,'stop_margin':stop_margin,'interrupted':interrupted},indent=2)+'\n')
assert p.returncode==0 and not interrupted and minimum>=floor
PY
meson introspect /build/compile --tests > /build/original-registered-tests.json
set +e
dbus-run-session -- meson test -C /build/compile --no-rebuild --print-errorlogs -j2 --suite miners-common --suite miner-fs --suite extract --no-suite slow > /build/original-tests.log 2>&1
result=$?
set -e
printf '%s\n' "$result" > /build/original-tests.exit
[[ $result == 0 ]]
meson install -C /build/compile --destdir /stage --no-rebuild
/build/compile/src/cli/localsearch --version > /build/cli-version.txt
python3 - <<'PY'
from pathlib import Path
import hashlib,json,os
p=Path('/build');rows=[json.loads(x) for x in (p/'compile/meson-logs/testlog.json').read_text().splitlines() if x.strip()]
assert len(rows)==13 and all(r['result']=='OK' and r['returncode']==0 for r in rows)
assert (p/'cli-version.txt').read_text().startswith('LocalSearch 3.11.1\n')
config=(p/'compile/config-miners.h').read_text()
assert '#define HAVE_LANDLOCK' in config.splitlines() and '#define HAVE_LIBSECCOMP' in config.splitlines()
registered=json.loads((p/'original-registered-tests.json').read_text());ran={r['name'] for r in rows}
s=os.statvfs('/build');assert s.f_bavail*s.f_frsize>=16*1024**3
r={'scope':'Frozen LocalSearch3.11.1 core miner/extractor/writeback with ICU/UPower/owned media metadata dependencies. Landlock explicitly enabled using upstream isolated distribution-build option; seccomp retained. Production release and original functional/sandbox programs compiled. Only13 non-slow common/indexer/extract utility programs executed on builder kernel; native functional/index/search/sandbox/cancellation/recovery and GUI acceptance remain pending. Optional absent format libraries remain auto-unavailable; man generation omitted because a2x is absent. No installed runtime or general parser-security claim.','compile_exit':0,'stage_exit':0,'kernel':os.uname().release,'original_tests':[{k:r[k] for k in ['name','result','returncode']} for r in rows],'registered_not_executed':[r['name'] for r in registered if not any(s.split(':',1)[-1]+' - localsearch:'+r['name'] in ran for s in r['suite'])],'resource':json.loads((p/'compile-resource.json').read_text()),'artifacts':{str(f.relative_to(p/'compile')):hashlib.sha256(f.read_bytes()).hexdigest() for f in (p/'compile').rglob('*') if f.is_file() and not f.is_symlink() and f.open('rb').read(4)==b'\x7fELF'},'stage_sha256':{str(f.relative_to('/stage')):hashlib.sha256(f.read_bytes()).hexdigest() for f in Path('/stage').rglob('*') if f.is_file() and not f.is_symlink()}}
(p/'stage-results.json').write_text(json.dumps(r,indent=2)+'\n')
PY
