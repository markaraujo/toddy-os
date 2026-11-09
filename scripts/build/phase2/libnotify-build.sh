#!/bin/bash
set -euo pipefail
[[ $(id -u) == 101 && ! -e /build/compile ]]
meson setup /build/compile /src --prefix=/usr --libdir=lib --buildtype=release \
    --wrap-mode=nofallback -Dtests=true -Dintrospection=enabled -Dman=false \
    -Dgtk_doc=false -Ddocbook_docs=disabled > /build/configure.log 2>&1
ninja -C /build/compile -j4 > /build/compile.log 2>&1
DESTDIR=/stage meson install -C /build/compile --no-rebuild > /build/stage.log 2>&1
cc -Wall -Wextra -Werror /src/toddy-probe.c -I/stage/usr/include \
    -L/stage/usr/lib -Wl,-rpath,/stage/usr/lib \
    $(pkg-config --cflags --libs gdk-pixbuf-2.0 gio-2.0) -lnotify -o /build/consumer
dbus-run-session -- env GIO_USE_PORTALS=0 /build/consumer > /build/consumer.log 2>&1
GI_TYPELIB_PATH=/stage/usr/lib/girepository-1.0 LD_LIBRARY_PATH=/stage/usr/lib python3 - <<'PY' > /build/gi.log 2>&1
import gi
gi.require_version('Notify','0.7')
from gi.repository import Notify
assert Notify.init('Toddy native GI')
n=Notify.Notification.new('Toddy','Native types',None)
assert n.props.summary=='Toddy' and n.props.body=='Native types'
Notify.uninit()
print('Native Notify0.7 GIR/typelib/initialization/properties; no displayed notification')
PY
python3 - <<'PY'
from pathlib import Path
import json
rows=json.loads(Path('/build/compile/meson-info/intro-tests.json').read_text())
assert rows==[], 'Unexpected registered suite; inspect and select affected original tests before promotion'
Path('/build/test-results.json').write_text(json.dumps({
    'scope':'Native notification library C/GI/empty-private-bus refusal only; no displayed GNOME notification or accessibility acceptance',
    'registered_upstream_tests':0,'upstream_status':'Original test setup requires optional Python dbus/dbusmock; unavailable, no upstream passes claimed. Actual graphical/interactive notification behavior remains for native GNOME.',
    'staged_consumer_exit':0,'gi_exit':0,'no_external_bus':True,
    'profile':'Native library, notify-send and Notify0.7 introspection; API docs/man dependencies omitted'
},indent=2)+'\n')
PY
