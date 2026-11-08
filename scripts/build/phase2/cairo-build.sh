#!/bin/bash
# Native Wayland GTK prerequisite; frozen BLFS states full visual suite not working.
set -euo pipefail
[[ $(id -u) == 101 && -d /stage ]]
ulimit -c 0
meson setup /build/compile /src --prefix=/usr --libdir=lib --buildtype=release \
    --default-library=shared --wrap-mode=nofallback -Dfontconfig=enabled \
    -Dfreetype=enabled -Dglib=enabled -Dpng=enabled -Dzlib=enabled \
    -Dxlib=disabled -Dxcb=disabled -Dxlib-xcb=disabled -Dtests=disabled \
    -Dspectre=disabled -Dlzo=disabled -Dsymbol-lookup=disabled -Dgtk_doc=false
ninja -C /build/compile -j4
meson test -C /build/compile --print-errorlogs --num-processes 4
python3 - <<'TEST'
import json
from pathlib import Path
p=Path('/build/compile/meson-logs/testlog.json')
rows=[json.loads(l) for l in p.read_text().splitlines()] if p.exists() else []
assert all(r['result']=='OK' and r['returncode']==0 for r in rows)
Path('/build/test-results.json').write_text(json.dumps({'full_upstream_suite':'not qualified; BLFS states not working','registered_driver_failures':0,'registered_drivers':[{'name':r['name'],'exit':r['returncode'],'seconds':r['duration']} for r in rows]},indent=2)+'\n')
TEST
DESTDIR=/stage ninja -C /build/compile install
[[ -f /stage/usr/lib/libcairo.so.2 && -f /stage/usr/lib/pkgconfig/cairo-gobject.pc ]]
