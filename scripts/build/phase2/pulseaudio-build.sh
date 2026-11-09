#!/bin/bash
set -euo pipefail
[[ $(id -u) == 101 && ! -e /build/compile && -d /src/toddy-test-sdk ]]
ln -s /src/toddy-test-sdk /build/test-sdk
export PKG_CONFIG_PATH=/build/test-sdk/lib/pkgconfig
export LD_LIBRARY_PATH=/build/test-sdk/lib
meson setup /build/compile /src --prefix=/usr --libdir=lib --buildtype=release \
    --wrap-mode=nofallback -Ddaemon=false -Dclient=true -Dtests=true -Dman=false \
    -Ddoxygen=false -Ddatabase=gdbm -Dbluez5=disabled -Dx11=disabled -Dgtk=disabled \
    -Doss-output=disabled -Dglib=enabled -Ddbus=enabled -Dsystemd=enabled \
    > /build/configure.log 2>&1
ninja -C /build/compile -j4 > /build/compile.log 2>&1
meson test -C /build/compile --no-rebuild --print-errorlogs > /build/upstream-tests.log 2>&1
DESTDIR=/stage meson install -C /build/compile --no-rebuild > /build/stage.log 2>&1
cc -Wall -Wextra -Werror /src/toddy-probe.c -I/stage/usr/include \
    -L/stage/usr/lib -L/stage/usr/lib/pulseaudio \
    -Wl,-rpath,/stage/usr/lib -Wl,-rpath,/stage/usr/lib/pulseaudio \
    $(PKG_CONFIG_PATH=/stage/usr/lib/pkgconfig pkg-config --cflags --libs libpulse libpulse-mainloop-glib glib-2.0) -o /build/consumer
LD_LIBRARY_PATH=/stage/usr/lib:/stage/usr/lib/pulseaudio /build/consumer > /build/consumer.log 2>&1
python3 - <<'PY'
from pathlib import Path
import json
w=Path('/build');rows=[json.loads(s) for s in (w/'compile/meson-logs/testlog.json').read_text().splitlines() if s.strip()]
assert rows and all(r['result']=='OK' and r['returncode']==0 for r in rows)
assert not (w/'stage/usr/bin/pulseaudio').exists()
(w/'test-results.json').write_text(json.dumps({'scope':'Native original Pulse client tests and sample/channel/volume/mainloop/refusal APIs; no server or audible-device acceptance','upstream_drivers':[{'name':r['name'],'exit':r['returncode']} for r in rows],'staged_consumer_exit':0,'profile':'Client libraries/tools only, GLib/DBus/systemd, no PulseAudio daemon/system user/units; Pipewire provides the future session server','private_check_sdk':'Reused qualified Check0.15.2, not installed'},indent=2)+'\n')
PY
