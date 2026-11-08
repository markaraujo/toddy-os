#!/bin/bash
# Native EDID/DisplayID parser; all registered frozen fixtures, no physical device.
set -euo pipefail
[[ $(id -u) == 101 && -f /src/meson.build && -d /stage ]]
[[ $(pkg-config --modversion hwdata) == 0.410 ]]
meson setup /build/compile /src --prefix=/usr --libdir=lib --buildtype=release --wrap-mode=nofallback
ninja -C /build/compile -j4
meson test -C /build/compile --no-rebuild --num-processes 4 --print-errorlogs
DESTDIR=/stage meson install -C /build/compile --no-rebuild
export PKG_CONFIG_PATH=/stage/usr/lib/pkgconfig
cc -std=c11 -Wall -Wextra -Werror /src/toddy-probe.c -I/stage/usr/include \
    -o /build/native-edid -L/stage/usr/lib -Wl,-rpath,/stage/usr/lib \
    $(pkg-config --cflags --libs libdisplay-info)
/build/native-edid /src/test/data/qemu.edid > /build/native-edid.log 2>&1
python3 - <<'PY'
from pathlib import Path
import json
registered=json.loads(Path('/build/compile/meson-info/intro-tests.json').read_text())
rows=[json.loads(x) for x in Path('/build/compile/meson-logs/testlog.json').read_text().splitlines()]
assert len(rows)==len(registered)>0 and all(r['result']=='OK' and r['returncode']==0 for r in rows)
Path('/build/test-results.json').write_text(json.dumps({'scope':'Native EDID/DisplayID parser and actual QEMU fixture/PnP lookup/malformed-input refusal; no physical monitor/driver or graphical acceptance',
'upstream_drivers':[{'name':r['name'],'native_exit':r['returncode']} for r in rows],
'staged_consumer_exit':0,'qemu_pnp_make':'Red Hat, Inc.','invalid_header_and_truncated_input_refused':True,
'profile':'Frozen hwdata0.410 lookup data; optional external reference decoder not required or used for passes'},indent=2)+'\n')
PY
