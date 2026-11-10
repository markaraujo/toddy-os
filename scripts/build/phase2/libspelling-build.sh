#!/bin/bash
set -euo pipefail
[[ $(id -u) == 101 && ! -e /build/compile ]]
export PYTHONDONTWRITEBYTECODE=1
ulimit -c 0
# Work resides in a bounded already allocated scratch filesystem; target source
# reserve is checked by preparation, independently of private compiler capacity.
python3 - <<'PY'
import os
s=os.statvfs('/build');assert s.f_bavail*s.f_frsize>=256*1024**2
PY
meson setup /build/compile /src --prefix=/usr --libdir=lib --buildtype=debugoptimized \
 --wrap-mode=nofallback -Ddocs=false -Dsysprof=false -Denchant=enabled -Dintrospection=enabled -Dvapi=false
ninja -C /build/compile -j4 > /build/original-build.log 2>&1
meson introspect /build/compile --tests > /build/original-registered-tests.json
meson test -C /build/compile --no-rebuild --print-errorlogs --num-processes 2 > /build/original-tests.log 2>&1
meson install -C /build/compile --destdir /stage --no-rebuild
GI_TYPELIB_PATH=/stage/usr/lib/girepository-1.0 LD_LIBRARY_PATH=/stage/usr/lib python3 /src/toddy-probe.py /build/consumer > /build/native-consumer.json
python3 - <<'PY'
from pathlib import Path
import hashlib,json,os
w=Path('/build');tests=[json.loads(s) for s in (w/'compile/meson-logs/testlog.json').read_text().splitlines() if s.strip()]
assert len(tests)==4 and all(t['result']=='OK' and t['returncode']==0 for t in tests)
s=os.statvfs(w);assert s.f_bavail*s.f_frsize>=256*1024**2
r={'scope':'Libspelling0.4.11 real owned Enchant/Aspell English backend, original four test programs, staged Spelling1 GI API. No graphical text-buffer adapter/editor acceptance. Optional Vala/documentation/profiler disabled; introspection/enchant enabled.','compile_exit':0,'stage_exit':0,'original_tests':tests,'consumer':json.loads((w/'native-consumer.json').read_text()),'scratch_free_bytes':s.f_bavail*s.f_frsize,'artifacts':{str(p.relative_to(w/'compile')):hashlib.sha256(p.read_bytes()).hexdigest() for p in (w/'compile').rglob('*') if p.is_file() and not p.is_symlink() and p.open('rb').read(4)==b'\x7fELF'},'stage_sha256':{str(p.relative_to(w/'stage')):hashlib.sha256(p.read_bytes()).hexdigest() for p in (w/'stage').rglob('*') if p.is_file() and not p.is_symlink()}}
(w/'stage-results.json').write_text(json.dumps(r,indent=2)+'\n')
PY
