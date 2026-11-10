#!/bin/bash
set -euo pipefail
[[ $(id -u) == 101 && ! -e /build/compile ]]
export PYTHONDONTWRITEBYTECODE=1
export PYTEST_ADDOPTS='-p no:cacheprovider --basetemp=/build/pytest-tmp --junitxml=/build/original-pytest.xml'
ulimit -c 0
meson setup /build/compile /src --prefix=/usr --libdir=lib --buildtype=release \
 --wrap-mode=nofallback -Dbackend-gtk3=enabled -Dbackend-gtk4=enabled \
 -Dbackend-qt5=disabled -Dbackend-qt6=disabled -Dintrospection=true \
 -Dvapi=false -Ddocs=false -Dtests=true -Dportal-tests=false
ninja -C /build/compile -j4
meson introspect /build/compile --tests > /build/original-registered-tests.json
python3 - <<'PY'
from pathlib import Path
import json
rows=json.loads(Path('/build/original-registered-tests.json').read_text());assert len(rows)==1 and rows[0]['name']=='pytest','Original tests must not disappear for missing pytest/dbusmock'
PY
set +e
meson test -C /build/compile --print-errorlogs -j1 > /build/original-tests.log 2>&1
result=$?
set -e
printf '%s\n' "$result" > /build/original-tests.exit
[[ $result == 0 ]]
meson install -C /build/compile --destdir /stage --no-rebuild
cc /src/toddy-probe.c -I/stage/usr/include -L/stage/usr/lib \
 $(pkg-config --cflags --libs gio-2.0) -lportal -Wl,-rpath,/stage/usr/lib -o /build/native-probe
dbus-run-session -- /build/native-probe > /build/native-consumer.json
for backend in 3 4; do
 GI_TYPELIB_PATH=/stage/usr/lib/girepository-1.0 LD_LIBRARY_PATH=/stage/usr/lib python3 - "$backend" <<'PY' > "/build/GI-gtk${backend}.json"
import gi,ctypes,json,sys
v=sys.argv[1];gi.require_version('Gtk',v+'.0');gi.require_version('Xdp','1.0');gi.require_version('XdpGtk'+v,'1.0')
from gi.repository import Xdp
module=__import__('gi.repository',fromlist=['XdpGtk'+v]);namespace=getattr(module,'XdpGtk'+v)
assert Xdp.Portal.__gtype__.name=='XdpPortal'
library=ctypes.CDLL('/stage/usr/lib/libportal-gtk'+v+'.so');assert getattr(library,'xdp_parent_new_gtk')
print(json.dumps({'namespace':'XdpGtk'+v+'1.0','base_GI_type':'XdpPortal','GTK_backend_symbol_loaded':True,'widget_or_parent_export_tested':False}))
PY
done
python3 - <<'PY'
from pathlib import Path
import hashlib,json,xml.etree.ElementTree as ET
p=Path('/build');rows=[json.loads(x) for x in (p/'compile/meson-logs/testlog.json').read_text().splitlines() if x.strip()];assert len(rows)==1 and rows[0]['result']=='OK' and rows[0]['returncode']==0
cases=ET.parse(p/'original-pytest.xml').getroot().findall('.//testcase');assert cases
r={'scope':'Frozen libportal0.9.1 base/GTK3/GTK4/GI; optional Qt backends (and Qt-only book patch), Vala/docs/demo omitted. All selected original pytest programs use private DBus/mock portal data, not actual desktop permissions/input/capture/screencast. Actual private-bus C construct/release/nonFlatpak-nonSnap and separate GTK3/GTK4 GI/shared-symbol checks only. No GNOME portal service/dialog/widget/permission grant acceptance.','compile_exit':0,'stage_exit':0,'original_tests':[{k:r[k] for k in ['name','result','returncode']} for r in rows],'original_pytest_cases':[{'name':c.get('name'),'failure':c.find('failure') is not None,'error':c.find('error') is not None,'skipped':c.find('skipped') is not None} for c in cases],'consumer':json.loads((p/'native-consumer.json').read_text()),'GI_consumers':[json.loads((p/('GI-gtk'+v+'.json')).read_text()) for v in ['3','4']],'artifacts':{str(f.relative_to(p/'compile')):hashlib.sha256(f.read_bytes()).hexdigest() for f in (p/'compile').rglob('*') if f.is_file() and not f.is_symlink() and f.open('rb').read(4)==b'\x7fELF'},'stage_sha256':{str(f.relative_to(p/'stage')):hashlib.sha256(f.read_bytes()).hexdigest() for f in (p/'stage').rglob('*') if f.is_file() and not f.is_symlink()}}
assert all(not c['failure'] and not c['error'] for c in r['original_pytest_cases']);(p/'stage-results.json').write_text(json.dumps(r,indent=2)+'\n')
PY
