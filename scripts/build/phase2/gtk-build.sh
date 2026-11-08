#!/bin/bash
set -euo pipefail
[[ $(id -u) == 101 && ! -e /build/compile ]]
ulimit -c 0
export PYTHONDONTWRITEBYTECODE=1
meson setup /build/compile /src --prefix=/usr --libdir=lib --buildtype=release --wrap-mode=nofallback \
    -Ddefault_library=shared -Dwayland-backend=true -Dx11-backend=false -Dbroadway-backend=false \
    -Dmedia-gstreamer=disabled -Dvulkan=disabled -Dprint-cups=disabled -Dprint-cpdb=disabled \
    -Dcloudproviders=disabled -Dtracker=disabled -Dcolord=disabled -Dsysprof=disabled -Daccesskit=disabled \
    -Dintrospection=enabled -Dbuild-testsuite=true -Dbuild-tests=false -Dbuild-examples=false \
    -Dbuild-demos=true -Ddocumentation=false -Dman-pages=false
ninja -C /build/compile -j4
python3 - <<'PY'
from pathlib import Path
import json,os,re,subprocess
selected={'bitset':'gtk','stringlist':'gtk','rgba':'gdk'}
results=[]
for name,subdir in selected.items():
    with Path('/build/upstream-'+name+'.log').open('xb') as log:
        r=subprocess.run(['/build/compile/testsuite/'+subdir+'/'+name,'--tap'],stdout=log,stderr=subprocess.STDOUT)
    Path('/build/upstream-'+name+'.exit').write_text(str(r.returncode)+'\n');assert r.returncode==0,name
    text=Path('/build/upstream-'+name+'.log').read_text();count=len(re.findall(r'^ok\s+\d+',text,re.M))
    assert count and not re.search(r'^not ok|#\s*SKIP',text,re.M)
    results.append({'name':name,'native_exit':0,'passed_cases':count})
Path('/build/upstream-selected.json').write_text(json.dumps(results,indent=2)+'\n')
PY
DESTDIR=/stage ninja -C /build/compile install
glib-compile-schemas --strict /stage/usr/share/glib-2.0/schemas
cc -Wall -Wextra -Werror /src/toddy-probe.c -I/stage/usr/include/gtk-4.0 -L/stage/usr/lib \
    $(PKG_CONFIG_PATH=/stage/usr/lib/pkgconfig pkg-config --cflags --libs gtk4) -o /build/gtk-consumer
LD_LIBRARY_PATH=/stage/usr/lib /build/gtk-consumer > /build/native-api.log
GI_TYPELIB_PATH=/stage/usr/lib/girepository-1.0 LD_LIBRARY_PATH=/stage/usr/lib python3 - <<'PY' > /build/native-gi.log
import gi
gi.require_version('Gtk','4.0');gi.require_version('Gdk','4.0');gi.require_version('Gsk','4.0')
from gi.repository import Gtk,Gdk,Gsk
assert (Gtk.get_major_version(),Gtk.get_minor_version(),Gtk.get_micro_version())==(4,22,4)
model=Gtk.StringList.new(['Toddy','Português']);assert model.get_n_items()==2 and model.get_string(1)=='Português'
color=Gdk.RGBA();assert color.parse('#002040')
assert Gsk.Transform.__gtype__.name=='GskTransform'
print('Native Gtk/Gdk/Gsk GI/version/Unicode model/color APIs, no graphical window')
PY
python3 - <<'PY'
from pathlib import Path
import json,hashlib,os
cache=Path('/stage/usr/share/glib-2.0/schemas/gschemas.compiled');assert cache.is_file()
fs=os.statvfs('/build');assert fs.f_bavail*fs.f_frsize>=128*1024**2
Path('/build/test-results.json').write_text(json.dumps({'scope':'Native bootstrap Wayland GTK APIs and selected headless source tests only; GUI/compositor/session/media runtime still pending',
    'upstream_selected':json.loads(Path('/build/upstream-selected.json').read_text()),'staged_consumer_exit':0,'gi_exit':0,
    'native_api_stdout':Path('/build/native-api.log').read_text(),'native_gi_stdout':Path('/build/native-gi.log').read_text(),
    'schema_cache_sha256':hashlib.sha256(cache.read_bytes()).hexdigest(),
    'pending':'Actual Wayland window/focus/actions/responsiveness, display-dependent upstream tests, media and integrated GNOME acceptance'},indent=2)+'\n')
PY
