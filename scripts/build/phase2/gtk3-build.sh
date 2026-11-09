#!/bin/bash
set -euo pipefail
[[ $(id -u) == 101 && ! -e /build/compile ]]
ulimit -c 0
export PYTHONDONTWRITEBYTECODE=1
meson setup /build/compile /src --prefix=/usr --libdir=lib --buildtype=release \
    --wrap-mode=nofallback -Ddefault_library=shared \
    -Dwayland_backend=true -Dx11_backend=false -Dbroadway_backend=false \
    -Dwin32_backend=false -Dquartz_backend=false -Dcloudproviders=false \
    -Dprofiler=false -Dtracker3=false -Dprint_backends=file -Dcolord=no \
    -Dgtk_doc=false -Dman=false -Dintrospection=true -Dtests=true \
    -Dinstalled_tests=false -Ddemos=false -Dexamples=false > /build/configure.log 2>&1
ninja -C /build/compile -j4 > /build/compile.log 2>&1
/build/compile/testsuite/gdk/rgba --tap > /build/upstream-rgba.log 2>&1
DESTDIR=/stage meson install -C /build/compile --no-rebuild > /build/stage.log 2>&1
glib-compile-schemas --strict /stage/usr/share/glib-2.0/schemas > /build/schema.log 2>&1
cc -Wall -Wextra -Werror /src/toddy-probe.c \
    -I/stage/usr/include/gtk-3.0 -I/stage/usr/lib/gtk-3.0/include \
    -L/stage/usr/lib -Wl,-rpath,/stage/usr/lib \
    $(PKG_CONFIG_PATH=/stage/usr/lib/pkgconfig pkg-config --cflags --libs gtk+-3.0) -o /build/consumer
LD_LIBRARY_PATH=/stage/usr/lib /build/consumer > /build/consumer.log 2>&1
GI_TYPELIB_PATH=/stage/usr/lib/girepository-1.0 LD_LIBRARY_PATH=/stage/usr/lib python3 - <<'PY' > /build/gi.log 2>&1
import gi
gi.require_version('Gtk','3.0');gi.require_version('Gdk','3.0')
from gi.repository import Gtk,Gdk
assert (Gtk.get_major_version(),Gtk.get_minor_version(),Gtk.get_micro_version())==(3,24,52)
adjustment=Gtk.Adjustment.new(42,0,100,1,10,0)
assert adjustment.get_value()==42
adjustment.set_value(43)
assert adjustment.get_value()==43
color=Gdk.RGBA();assert color.parse('#002040')
print('Native Gtk/Gdk3.0 GIR/typelib/version/non-widget adjustment/navy color; no graphical window')
PY
python3 - <<'PY'
from pathlib import Path
import hashlib,json,re
work=Path('/build');text=(work/'upstream-rgba.log').read_text()
cases=re.findall(r'^ok\s+\d+[^\n]*',text,re.M)
assert len(cases)==4 and not re.search(r'^not ok|#\s*SKIP',text,re.M)
cache=work/'stage/usr/share/glib-2.0/schemas/gschemas.compiled';assert cache.is_file()
(work/'test-results.json').write_text(json.dumps({
    'scope':'Native GTK3 Wayland bootstrap/headless APIs only; no graphical window, GDM/GNOME/login/print/X11 or display-dependent test acceptance',
    'original_rgba_cases':4,'staged_consumer_exit':0,'gi_exit':0,'private_schema_exit':0,
    'schema_cache_sha256':hashlib.sha256(cache.read_bytes()).hexdigest(),
    'profile':'GTK3 Wayland/GI/file-print bootstrap, alongside accepted GTK4; no demos/examples or optional X11/Broadway/cloud/tracker/profiler/CUPS',
    'pending':'Actual native display/window/focus/actions/responsiveness, display-dependent original tests and owned schema/resource-cache union before promotion'
},indent=2)+'\n')
PY
