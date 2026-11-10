#!/bin/bash
set -euo pipefail
[[ $(id -u) == 101 && ! -e /build/compile ]]
export PYTHONDONTWRITEBYTECODE=1
ulimit -c 0
meson setup /build/compile /src --prefix=/usr --libdir=lib --buildtype=release --wrap-mode=nofallback -Dgtk_doc=false -Dintrospection=true -Dsendto=true
ninja -C /build/compile -j4 > /build/original-build.log 2>&1
meson introspect /build/compile --tests > /build/original-registered-tests.json
meson test -C /build/compile --no-rebuild --print-errorlogs test-bluetooth-device-test test-bluetooth-device-utils > /build/original-core-tests.log 2>&1
meson install -C /build/compile --destdir /stage --no-rebuild
python3 - <<'PY'
from pathlib import Path
import hashlib,json,os
w=Path('/build');tests=[json.loads(x) for x in (w/'compile/meson-logs/testlog.json').read_text().splitlines() if x.strip()];assert len(tests)==2 and all(t['result']=='OK' and t['returncode']==0 for t in tests)
registered=json.loads((w/'original-registered-tests.json').read_text());selected={'test-bluetooth-device-test','test-bluetooth-device-utils'};deferred=[t['name'] for t in registered if t['name'] not in selected];assert not any('skipped' in x for x in deferred), 'Keep actual mock integration programs available, not dependency skips'
assert Path('/stage/usr/lib/pkgconfig/gnome-bluetooth-ui-3.0.pc').is_file()
r={'scope':'Frozen GNOME Bluetooth47.2 core/UI/GI/sendto compiled; two original non-display C programs only. Original private mock-bus/session integration programs compiled/deferred, not passes. No real Bluetooth adapter/pairing/transfer/UI/Settings/GNOME/hardware acceptance.','compile_exit':0,'stage_exit':0,'original_core_tests':tests,'original_registered_tests':registered,'original_deferred_tests':deferred,'artifacts':{str(p.relative_to(w/'compile')):hashlib.sha256(p.read_bytes()).hexdigest() for p in (w/'compile').rglob('*') if p.is_file() and not p.is_symlink() and p.open('rb').read(4)==b'\x7fELF'},'stage_sha256':{str(p.relative_to('/stage')):hashlib.sha256(p.read_bytes()).hexdigest() for p in Path('/stage').rglob('*') if p.is_file() and not p.is_symlink()}}
(w/'stage-results.json').write_text(json.dumps(r,indent=2)+'\n');s=os.statvfs('/build');assert s.f_bavail*s.f_frsize>=512*1024**2
PY
