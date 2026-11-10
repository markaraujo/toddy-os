#!/bin/bash
set -euo pipefail
[[ $(id -u) == 101 && -d /build/compile && ! -e /build/stage-results.json && ! -e /build/ELFs-before-stage-2.json ]]
export PYTHONDONTWRITEBYTECODE=1
python3 - <<'PY2'
from pathlib import Path
import hashlib,json
p=Path('/build');rows=json.loads((p/'original-registered-tests.json').read_text());assert len(rows)==1 and rows[0]['name']=='test-utils'
r={str(f.relative_to(p/'compile')):hashlib.sha256(f.read_bytes()).hexdigest() for f in (p/'compile').rglob('*') if f.is_file() and not f.is_symlink() and f.open('rb').read(4)==b'\x7fELF'};assert len(r)==101
(p/'ELFs-before-stage-2.json').write_text(json.dumps(r,indent=2)+'\n')
PY2
meson test -C /build/compile --no-rebuild --print-errorlogs -j1 > /build/original-tests.log 2>&1
meson install -C /build/compile --destdir /stage --no-rebuild
for major in 3 4; do
 if [[ $major == 3 ]]; then gtk_package=gtk+-3.0; nma_library=nma; else gtk_package=gtk4; nma_library=nma-gtk4; fi
 cc /src/toddy-probe.c -DTODDY_GTK_MAJOR="$major" -I/stage/usr/include/libnma -L/stage/usr/lib \
  $(pkg-config --cflags --libs "$gtk_package" libnm) -l"$nma_library" -Wl,-rpath,/stage/usr/lib -o /build/native-probe-"$major"
 LD_LIBRARY_PATH=/stage/usr/lib /build/native-probe-"$major" > /build/native-consumer-"$major".json
 GI_TYPELIB_PATH=/stage/usr/lib/girepository-1.0 LD_LIBRARY_PATH=/stage/usr/lib python3 - "$major" > /build/native-GI-"$major".json <<'GI'
import gi,json,sys
major=int(sys.argv[1]);namespace='NMA' if major==3 else 'NMA4'
gi.require_version('Gtk',str(major)+'.0');gi.require_version(namespace,'1.0')
from gi.repository import Gtk,GObject
module=__import__('gi.repository',fromlist=[namespace]).__dict__[namespace]
assert Gtk.get_major_version()==major
assert GObject.type_is_a(module.WifiDialog.__gtype__,Gtk.Dialog.__gtype__)
assert GObject.type_is_a(module.CertChooser.__gtype__,Gtk.Widget.__gtype__)
assert module.MobileProvidersDatabase.__gtype__
print(json.dumps({'namespace':namespace+'1.0','GTK_major':major,'public_widget_and_mobile_types':True,'actual_widget_open_tested':False}))
GI
done
python3 - <<'PY'
from pathlib import Path
import hashlib,json
p=Path('/build');consumers={str(major):json.loads((p/('native-consumer-'+str(major)+'.json')).read_text()) for major in [3,4]}
before=json.loads((p/'ELFs-before-stage-2.json').read_text());assert all(hashlib.sha256((p/'compile'/name).read_bytes()).hexdigest()==sha for name,sha in before.items())
rows=[json.loads(x) for x in (p/'compile/meson-logs/testlog.json').read_text().splitlines() if x.strip()];assert len(rows)==1 and rows[0]['name']=='libnma:test-utils' and rows[0]['result']=='OK' and rows[0]['returncode']==0
r={'scope':'Actual GTK3 and GTK4 libnma1.10.6/GI/Vala with owned Gcr4 certificate support and ISO codes. One original test-utils driver; sixteen manual GTK executables compile only. Own widget type/GTK ABI and libnm refusal/recovery consumers, NOT actual widget open/focus, credentials/WiFi/network/GNOME acceptance. Optional cellular provider DB omitted.','compile_exit':0,'stage_exit':0,'original_registered_tests':json.loads((p/'original-registered-tests.json').read_text()),'original_tests':[{k:r[k] for k in ['name','result','returncode']} for r in [json.loads(x) for x in (p/'compile/meson-logs/testlog.json').read_text().splitlines() if x.strip()]],'unchanged_original_elfs':json.loads((p/'ELFs-before-stage-2.json').read_text()),'consumers':consumers,'artifacts':{str(f.relative_to(p/'compile')):hashlib.sha256(f.read_bytes()).hexdigest() for f in (p/'compile').rglob('*') if f.is_file() and not f.is_symlink() and f.open('rb').read(4)==b'\x7fELF'},'stage_sha256':{str(f.relative_to(p/'stage')):hashlib.sha256(f.read_bytes()).hexdigest() for f in (p/'stage').rglob('*') if f.is_file() and not f.is_symlink()}}
(p/'stage-results.json').write_text(json.dumps(r,indent=2)+'\n')
PY
