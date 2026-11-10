#!/bin/bash
set -euo pipefail
[[ $(id -u) == 101 && ! -e /build/compile ]]
export PYTHONDONTWRITEBYTECODE=1
ulimit -c 0
meson setup /build/compile /src --prefix=/usr --libdir=lib --buildtype=release \
 --wrap-mode=nofallback -Dintrospection=enabled -Dvapi=true -Dtests=true \
 -Dexamples=false -Dgtk_doc=false -Dglade_catalog=disabled
ninja -C /build/compile -j4
meson introspect /build/compile --tests > /build/original-registered-tests.json
# All registered upstream programs initialize GTK and need a real display.
# Compile them, preserve their identities, and leave execution explicitly pending.
meson install -C /build/compile --destdir /stage --no-rebuild
cc /src/toddy-probe.c -I/stage/usr/include/libhandy-1 -L/stage/usr/lib \
 $(pkg-config --cflags --libs gtk+-3.0) -lhandy-1 -Wl,-rpath,/stage/usr/lib -o /build/native-probe
LD_LIBRARY_PATH=/stage/usr/lib /build/native-probe > /build/native-consumer.json
GI_TYPELIB_PATH=/stage/usr/lib/girepository-1.0 LD_LIBRARY_PATH=/stage/usr/lib python3 - <<'PY' > /build/GI-consumer.json
"""Use the actual introspectable ValueObject.new(GValue) constructor."""
import gi,json
gi.require_version('Handy','1')
from gi.repository import Handy,GObject
v=GObject.Value();v.init(GObject.TYPE_STRING);v.set_string('Toddy ã')
obj=Handy.ValueObject.new(v);v.set_string('changed')
assert obj.get_string()=='Toddy ã' and obj.dup_string()=='Toddy ã'
print(json.dumps({'namespace':'Handy1','UTF8_value_object':True,'widget_or_display_tested':False}))
PY
python3 - <<'PY'
from pathlib import Path
import hashlib,json
p=Path('/build');rows=json.loads((p/'original-registered-tests.json').read_text());assert len(rows)==30
r={'scope':'Frozen libhandy1.8.3 GTK3/GI/Vala required by GNOME Terminal. All30original graphical programs compiled/deferred until actual native display; NONE executed or passed here. Own C/GI non-widget Unicode/value ownership/enum/two reset cycles only. Optional examples/Glade/docs omitted. No GUI/focus/Terminal acceptance.','compile_exit':0,'stage_exit':0,'original_tests_passed':0,'original_graphical_tests_pending':[r['name'] for r in rows],'consumer':json.loads((p/'native-consumer.json').read_text()),'GI_consumer':json.loads((p/'GI-consumer.json').read_text()),'artifacts':{str(f.relative_to(p/'compile')):hashlib.sha256(f.read_bytes()).hexdigest() for f in (p/'compile').rglob('*') if f.is_file() and not f.is_symlink() and f.open('rb').read(4)==b'\x7fELF'},'stage_sha256':{str(f.relative_to(p/'stage')):hashlib.sha256(f.read_bytes()).hexdigest() for f in (p/'stage').rglob('*') if f.is_file() and not f.is_symlink()}}
(p/'stage-results.json').write_text(json.dumps(r,indent=2)+'\n')
PY
