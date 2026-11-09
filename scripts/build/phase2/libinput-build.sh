#!/bin/bash
set -euo pipefail
[[ $(id -u) == 101 && ! -e /build/compile && -d /src/toddy-test-sdk ]]
ln -s /src/toddy-test-sdk /build/test-sdk
export PKG_CONFIG_PATH=/build/test-sdk/lib/pkgconfig
export LD_LIBRARY_PATH=/build/test-sdk/lib
meson setup /build/compile /src --prefix=/usr --libdir=lib --buildtype=release \
    --wrap-mode=nofallback -Dtests=true -Dinstall-tests=false -Dlibwacom=false \
    -Dmtdev=true -Ddebug-gui=false -Ddocumentation=false -Dzshcompletiondir=no \
    -Dinternal-event-debugging=false -Dautoload-plugins=false -Dlua-plugins=disabled \
    > /build/configure.log 2>&1
ninja -C /build/compile -j4 > /build/compile.log 2>&1
meson test -C /build/compile --no-rebuild --no-suite hardware --print-errorlogs \
    > /build/upstream-tests.log 2>&1
DESTDIR=/stage meson install -C /build/compile --no-rebuild > /build/stage.log 2>&1
cc -std=c11 -Wall -Wextra -Werror /src/toddy-probe.c -I/stage/usr/include \
    -L/stage/usr/lib -Wl,-rpath,/stage/usr/lib \
    $(PKG_CONFIG_PATH=/stage/usr/lib/pkgconfig pkg-config --cflags --libs libinput) -o /build/consumer
/build/consumer > /build/consumer.log 2>&1
python3 - <<'PY'
from pathlib import Path
import json
rows=[json.loads(s) for s in Path('/build/compile/meson-logs/testlog.json').read_text().splitlines() if s.strip()]
assert rows
for r in rows:
    assert (r['result']=='OK' and r['returncode']==0) or (r['result']=='SKIP' and r['returncode']==77)
registered=json.loads(Path('/build/compile/meson-info/intro-tests.json').read_text())
Path('/build/test-results.json').write_text(json.dumps({
    'scope':'Native portable libinput tests/API only; no device events, graphical input, tablet or physical acceptance',
    'selected_drivers':[{'name':r['name'],'result':r['result'],'exit':r['returncode']} for r in rows],
    'hardware_drivers_not_selected':[r['name'] for r in registered if any(s.endswith(':hardware') or s=='hardware' for s in r['suite'])],
    'staged_consumer_exit':0,'private_check_sdk':'Reused qualified Check0.15.2, not installed',
    'profile':{'mtdev':True,'libwacom':False,'lua_plugins':False,'internal_event_debugging':False,'debug_gui':False},
    'limitations':'Root/uinput SKIP77 and omitted hardware suites are untested; libwacom tablet identification and optional Lua plugins unavailable'
},indent=2)+'\n')
PY
