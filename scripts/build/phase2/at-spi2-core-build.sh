#!/bin/bash
# Frozen GNOME50 accessibility core; Wayland profile, real private-bus tests.
set -euo pipefail
[[ $(id -u) == 101 && -f /src/meson.build && -d /stage ]]
meson setup /build/compile /src --prefix=/usr --libdir=lib --buildtype=release \
    --wrap-mode=nofallback -Dx11=disabled -Dgtk2_atk_adaptor=false \
    -Ddefault_bus=dbus-daemon -Duse_systemd=true -Dintrospection=enabled -Ddocs=false
ninja -C /build/compile -j4
dbus-run-session -- python3 /src/toddy-private-bus.py full
DESTDIR=/stage ninja -C /build/compile install
export PKG_CONFIG_PATH=/stage/usr/lib/pkgconfig
cc /src/toddy-probe.c -I/stage/usr/include/atk-1.0 -I/stage/usr/include/at-spi-2.0 \
    -o /build/native-states -L/stage/usr/lib -Wl,-rpath,/stage/usr/lib \
    $(pkg-config --cflags --libs atk atspi-2)
/build/native-states > /build/native-states.log 2>&1
GI_TYPELIB_PATH=/stage/usr/lib/girepository-1.0 LD_LIBRARY_PATH=/stage/usr/lib python3 -B - <<'GI' > /build/native-gi.log 2>&1
import gi
gi.require_version('Atk','1.0')
gi.require_version('Atspi','2.0')
from gi.repository import Atk,Atspi
a=Atk.StateSet.new()
assert a.add_state(Atk.StateType.FOCUSED) and a.contains_state(Atk.StateType.FOCUSED)
assert a.remove_state(Atk.StateType.FOCUSED) and not a.contains_state(Atk.StateType.FOCUSED)
b=Atspi.StateSet.new([])
b.add(Atspi.StateType.FOCUSED)
assert b.contains(Atspi.StateType.FOCUSED)
b.remove(Atspi.StateType.FOCUSED)
assert not b.contains(Atspi.StateType.FOCUSED)
GI
python3 - <<'PY'
from pathlib import Path
import json
registered=json.loads(Path('/build/compile/meson-info/intro-tests.json').read_text())
rows=[json.loads(l) for l in Path('/build/compile/meson-logs/testlog.json').read_text().splitlines() if l.strip()]
assert len(rows)==len(registered)>0 and all(r['result']=='OK' and r['returncode']==0 for r in rows)
Path('/build/test-results.json').write_text(json.dumps({'scope':'Native Wayland accessibility core/private D-Bus upstream fixtures/API/GI; not graphical or complete native desktop acceptance',
    'upstream_drivers':[{'name':r['name'],'native_exit':r['returncode']} for r in rows],
    'staged_consumer_exit':0,'gi_exit':0,'profile':'Full ATK+AT-SPI core/bridge, dbus-daemon/systemd integration; optional X11 and GTK2 module disabled'},indent=2)+'\n')
PY
