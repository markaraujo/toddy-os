#!/bin/bash
set -euo pipefail
[[ $(id -u) == 101 && ! -e /build/compile ]]
export PYTHONDONTWRITEBYTECODE=1
meson setup /build/compile /src --prefix=/usr --libdir=lib \
    --buildtype=release --wrap-mode=nodownload -Drelease=true \
    -Ddocs=false -Dtests=true -Dvapi=false -Dintrospection=true \
    -Dconfig-kde=false -Dconfig-osx=false -Dconfig-windows=false
ninja -C /build/compile -j4
meson test -C /build/compile --print-errorlogs -j1 > /build/original-tests.log 2>&1
meson install -C /build/compile --destdir /stage --no-rebuild
cc /src/toddy-probe.c -I/stage/usr/include/libproxy -L/stage/usr/lib \
    $(pkg-config --cflags --libs gobject-2.0) -lproxy \
    -Wl,-rpath,/stage/usr/lib -Wl,-rpath-link,/stage/usr/lib/libproxy \
    -o /build/native-probe
LD_LIBRARY_PATH=/stage/usr/lib:/stage/usr/lib/libproxy /build/native-probe > /build/native-consumer.json
python3 - <<'PY'
from pathlib import Path
import hashlib,json
p=Path('/build');tests=[json.loads(s) for s in (p/'compile/meson-logs/testlog.json').read_text().splitlines() if s.strip()]
assert len(tests)==5 and all(r['result']=='OK' and r['returncode']==0 for r in tests)
result={'scope':'Five original libproxy/manager/environment/sysconfig/GNOME drivers including private loopback PAC/Duktape fixtures; actual public API direct/bypass/malformed-URI safe fallback and lifecycle. No remote proxy/WPAD/native desktop acceptance.', 'compile_exit':0,'stage_exit':0,'original_tests':[{k:r[k] for k in ['name','result','returncode']} for r in tests], 'consumer':json.loads((p/'native-consumer.json').read_text()), 'artifacts':{str(f.relative_to(p/'compile')):hashlib.sha256(f.read_bytes()).hexdigest() for f in (p/'compile').rglob('*') if f.is_file() and not f.is_symlink() and f.open('rb').read(4)==b'\x7fELF'},'stage_sha256':{str(f.relative_to(p/'stage')):hashlib.sha256(f.read_bytes()).hexdigest() for f in (p/'stage').rglob('*') if f.is_file() and not f.is_symlink()}}
(p/'stage-results.json').write_text(json.dumps(result,indent=2)+'\n')
PY
