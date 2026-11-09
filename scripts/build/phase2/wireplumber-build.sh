#!/bin/bash
set -euo pipefail
[[ $(id -u) == 101 && ! -e /build/compile ]]
meson setup /build/compile /src --prefix=/usr --libdir=lib --sysconfdir=/etc \
    --buildtype=release --wrap-mode=nofallback -Dsystem-lua=true \
    -Dsystemd=enabled -Delogind=disabled -Dsystemd-system-service=false \
    -Dsystemd-user-service=true -Ddoc=disabled -Dintrospection=disabled \
    -Dtests=true -Ddbus-tests=true > /build/configure.log 2>&1
ninja -C /build/compile -j4 > /build/compile.log 2>&1
meson test -C /build/compile --no-rebuild --print-errorlogs > /build/upstream-tests.log 2>&1
DESTDIR=/stage meson install -C /build/compile --no-rebuild > /build/stage.log 2>&1
cc -Wall -Wextra -Werror /src/toddy-probe.c \
    -I/stage/usr/include/wireplumber-0.5 -L/stage/usr/lib -Wl,-rpath,/stage/usr/lib \
    $(pkg-config --cflags --libs gio-2.0 libpipewire-0.3) -lwireplumber-0.5 -o /build/consumer
export LD_LIBRARY_PATH=/stage/usr/lib
/build/consumer > /build/consumer.log 2>&1
/stage/usr/bin/wireplumber --version > /build/version.log 2>&1
python3 - <<'PY'
from pathlib import Path
import json
rows=[json.loads(s) for s in Path('/build/compile/meson-logs/testlog.json').read_text().splitlines() if s.strip()]
assert rows and all((r['result']=='OK' and r['returncode']==0) or (r['result']=='SKIP' and r['returncode']==77) for r in rows)
Path('/build/test-results.json').write_text(json.dumps({'scope':'Native Wireplumber original tests/library/core/refusal/CLI only; no actual device routing, audible or GNOME acceptance',
    'upstream_drivers':[{'name':r['name'],'result':r['result'],'exit':r['returncode']} for r in rows],
    'staged_consumer_exit':0,'cli_version_exit':0,
    'profile':'Pinned system Lua5.4.8 and owned Pipewire1.6.8; no network subproject fetch, systemd user service only; PAM/login integration pending native session'},indent=2)+'\n')
PY
