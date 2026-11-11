#!/bin/bash
set -euo pipefail
[[ $(id -u) == 101 && -f /build/obj/config.status && ! -e /build/firefox-compile-result.json ]]
[[ $(cat /src/browser/config/version.txt) == 153.7.0 ]]
ulimit -c 0
export PYTHONDONTWRITEBYTECODE=1
export PATH=/tools/nasm/usr/bin:/usr/bin:/usr/sbin
export CC=clang CXX=clang++
export WASM_CC=/tools/wasi-sdk/bin/clang WASM_CXX=/tools/wasi-sdk/bin/clang++
export MOZCONFIG=/build/mozconfig MOZBUILD_STATE_PATH=/build/mozbuild
export MACH_BUILD_PYTHON_NATIVE_PACKAGE_SOURCE=none CARGO_HOME=/build/cargo-home
unset MOZ_TELEMETRY_REPORTING
cd /build
python3 - <<'PY'
from pathlib import Path
import hashlib,json,os,signal,subprocess,time
work=Path('/build');log=work/'firefox-compile-1.log'
assert not log.exists()
status=work/'obj/config.status';config=work/'mozconfig'
inputs={'config_status':hashlib.sha256(status.read_bytes()).hexdigest(),
        'mozconfig':hashlib.sha256(config.read_bytes()).hexdigest()}
floor=128*1024**2;margin=64*1024**2
def available():
    s=os.statvfs(work);return s.f_bavail*s.f_frsize
initial=available();assert initial>floor+margin
started=time.monotonic();minimum=initial;stopped=False
command=['/src/mach','build','-j6']
row={'state':'running','command':command,'inputs':inputs,'initial_free':initial,
     'reserve':floor,'stop_margin':margin,'pid':os.getpid(),
     'start_ticks':Path('/proc/self/stat').read_text().split()[21]}
receipt=work/'firefox-compile-result.json'
receipt.write_text(json.dumps(row,indent=2)+'\n')
with log.open('xb') as output:
    process=subprocess.Popen(command,stdout=output,stderr=subprocess.STDOUT,start_new_session=True)
    while process.poll() is None:
        minimum=min(minimum,available())
        if minimum<floor+margin:
            stopped=True;os.killpg(process.pid,signal.SIGINT)
            try:process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid,signal.SIGTERM)
                try:process.wait(timeout=10)
                except subprocess.TimeoutExpired:os.killpg(process.pid,signal.SIGKILL);process.wait(timeout=10)
            break
        time.sleep(1)
    result=process.wait()
row.update(state='compiler-returned',exit=result,elapsed_seconds=round(time.monotonic()-started,3),
           minimum_free=minimum,final_free=available(),interrupted_for_reserve=stopped)
receipt.write_text(json.dumps(row,indent=2)+'\n')
assert result==0 and not stopped and row['final_free']>=floor,row
artifacts={}
for name in ['firefox','libxul.so']:
    p=work/'obj/dist/bin'/name
    assert p.resolve().is_relative_to(work/'obj')
    with p.open('rb') as f:
        assert f.read(4)==b'\x7fELF',name
        f.seek(0);artifacts[name]=hashlib.file_digest(f,'sha256').hexdigest()
assert 'Version=153.7.0' in (work/'obj/dist/bin/application.ini').read_text()
row.update(state='compiled',artifacts=artifacts,
           scope='Source compiler outputs only; no stage/install/native browser/runtime sandbox acceptance')
receipt.write_text(json.dumps(row,indent=2)+'\n');print(json.dumps(row))
PY
