#!/bin/bash
set -euo pipefail
[[ $(id -u) == 101 && ! -e /build/compile ]]
export PYTHONDONTWRITEBYTECODE=1
ulimit -c 0
meson setup /build/compile /src --prefix=/usr --libdir=lib --buildtype=release --wrap-mode=nofallback
ninja -C /build/compile -j4 > /build/original-build.log 2>&1
meson introspect /build/compile --tests > /build/original-registered-tests.json
python3 - <<'PY'
from pathlib import Path
import json,subprocess
w=Path('/build');tests=json.loads((w/'original-registered-tests.json').read_text())
if tests:
 with (w/'original-tests.log').open('xb') as out:r=subprocess.run(['meson','test','-C','/build/compile','--no-rebuild','--print-errorlogs'],stdout=out,stderr=subprocess.STDOUT)
 assert r.returncode==0
 results=[json.loads(l) for l in (w/'compile/meson-logs/testlog.json').read_text().splitlines() if l.strip()];assert len(results)==len(tests) and all(t['result']=='OK' and t['returncode']==0 for t in results)
else:results=[]
(w/'original-test-results.json').write_text(json.dumps({'registered':tests,'results':results,'no_registered_tests_not_a_pass':not tests},indent=2)+'\n')
PY
meson install -C /build/compile --destdir /stage --no-rebuild
python3 - <<'PY'
from pathlib import Path
import hashlib,json,os
w=Path('/build');assert Path('/stage/usr/bin/tecla').is_file()
assert 'Version: 50.0' in Path('/stage/usr/share/pkgconfig/tecla.pc').read_text()
r={'scope':'Tecla50.0 keyboard previewer pinned to frozen BLFS source instead of moving control-center wrap HEAD. Compile/stage/data-only pkgconfig only; CLI initializes Adwaita before options and requires a separate native display test; no graphical keyboard preview/focus/input acceptance. Existing GTK/Adwaita/XKB evidence reused.','compile_exit':0,'stage_exit':0,'original_tests':json.loads((w/'original-test-results.json').read_text()),'consumer':{'pkgconfig_version':'50.0','CLI_requires_display':True,'CLI_tested':False,'graphical_viewer_tested':False},'artifacts':{str(p.relative_to(w/'compile')):hashlib.sha256(p.read_bytes()).hexdigest() for p in (w/'compile').rglob('*') if p.is_file() and not p.is_symlink() and p.open('rb').read(4)==b'\x7fELF'},'stage_sha256':{str(p.relative_to(w/'stage')):hashlib.sha256(p.read_bytes()).hexdigest() for p in (w/'stage').rglob('*') if p.is_file() and not p.is_symlink()}}
(w/'stage-results.json').write_text(json.dumps(r,indent=2)+'\n')
s=os.statvfs('/build');assert s.f_bavail*s.f_frsize>=16*1024**3
PY
