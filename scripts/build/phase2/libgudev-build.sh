#!/bin/bash
set -euo pipefail
[[ $(id -u) == 101 && ! -e /build/compile ]]
meson setup /build/compile /src --prefix=/usr --libdir=lib --buildtype=release \
    --wrap-mode=nofallback -Dtests=auto -Dintrospection=enabled -Dvapi=disabled \
    -Dgtk_doc=false > /build/configure.log 2>&1
ninja -C /build/compile -j4 > /build/compile.log 2>&1
DESTDIR=/stage meson install -C /build/compile --no-rebuild > /build/stage.log 2>&1
# Reproduce the original non-umockdev test target declaration explicitly; the
# upstream tests subdir is otherwise wholly omitted when umockdev is missing.
cc -D_GUDEV_COMPILATION -I/src -I/build/compile \
    /src/tests/test-gudevdevice.c /src/gudev/gudevdevice.c \
    -L/stage/usr/lib -Wl,-rpath,/stage/usr/lib \
    $(pkg-config --cflags --libs gio-2.0 libudev) -lgudev-1.0 -o /build/upstream-tags
/build/upstream-tags > /build/upstream-tags.log 2>&1
cc -Wall -Wextra -Werror /src/toddy-probe.c -I/stage/usr/include/gudev-1.0 \
    -L/stage/usr/lib -Wl,-rpath,/stage/usr/lib \
    $(pkg-config --cflags --libs gobject-2.0) -lgudev-1.0 -o /build/consumer
/build/consumer > /build/consumer.log 2>&1
GI_TYPELIB_PATH=/stage/usr/lib/girepository-1.0 LD_LIBRARY_PATH=/stage/usr/lib python3 - <<'PY' > /build/gi.log 2>&1
import gi
gi.require_version('GUdev','1.0')
from gi.repository import GUdev
client=GUdev.Client.new(None)
assert client is not None
assert client.query_by_sysfs_path('/sys/devices/toddy-nonexistent') is None
print('Native GUdev1.0 typelib/client/absent-path API, no device detection claim')
PY
python3 - <<'PY'
from pathlib import Path
import json,re
assert json.loads(Path('/build/compile/meson-info/intro-tests.json').read_text())==[]
text=Path('/build/upstream-tags.log').read_text()
assert re.search(r'^ok 1 /gudev/tags$',text,re.M) and re.search(r'^1[.][.]1$',text,re.M)
Path('/build/test-results.json').write_text(json.dumps({
    'scope':'Native GUdev GObject/C/GI/negative queries and original environment-based tag fixture only; no real device/udev event/GNOME acceptance',
    'original_portable_driver':'Unchanged test-gudevdevice.c plus gudevdevice.c, exact upstream target sources/define; tags1case exit0',
    'upstream_tag_cases':1,'staged_consumer_exit':0,'gi_exit':0,
    'not_selected':'Three umockdev-dependent original suites unavailable, not passes; no sysfs/device exposure added to compiler isolation',
    'profile':'GUdev shared library/introspection; optional Vala bindings and docs omitted'
},indent=2)+'\n')
PY
