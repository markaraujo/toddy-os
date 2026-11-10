#!/bin/bash
set -euo pipefail
[[ $(id -u) == 101 && ! -e /build/compile ]]
export PYTHONDONTWRITEBYTECODE=1
ulimit -c 0
meson setup /build/compile /src --prefix=/usr --libdir=lib --buildtype=release --wrap-mode=nofallback -Dgtk4=true -Dgtk3=true -Dvapi=false -Ddocs=false -Dman=false
ninja -C /build/compile -j4 > /build/original-build.log 2>&1
meson introspect /build/compile --tests > /build/original-registered-tests.json
# Both original tests create real GTK windows and need a qualified display/profile.
# Compile and inventory them; they are unexecuted, never counted as passes.
meson install -C /build/compile --destdir /stage --no-rebuild
for pc in colord-gtk colord-gtk4; do
    cc /src/toddy-probe.c -I/stage/usr/include/colord-1 -L/stage/usr/lib \
       $(PKG_CONFIG_PATH=/stage/usr/lib/pkgconfig pkg-config --cflags --libs "$pc" gio-2.0) -o "/build/$pc-probe"
    LD_LIBRARY_PATH=/stage/usr/lib "/build/$pc-probe" > "/build/$pc-probe.log"
done
python3 - <<'PY'
from pathlib import Path
import hashlib,json,os
w=Path('/build');registered=json.loads((w/'original-registered-tests.json').read_text());assert {t['name'] for t in registered}=={'colord-test-private','colord-gtk4-test-private'}
options={r['name']:r['value'] for r in json.loads((w/'compile/meson-info/intro-buildoptions.json').read_text())}
assert all(options[n] for n in ['gtk3','gtk4','introspection','tests']) and not options['gtk2'] and not options['vapi']
consumers={name:(w/(name+'-probe.log')).read_text() for name in ['colord-gtk','colord-gtk4']}
assert all(v=='Colord GTK local GObject/profile-empty state/two fresh cycles; no widget/display/service access\n' for v in consumers.values())
r={'scope':'Frozen colord-gtk0.3.1 GTK3+GTK4 libraries, GTK3 GI; optional Vala omitted because owned Colord has no VAPI. Both original display/profile tests compiled but unexecuted, not passes. Actual separate C consumers create only local non-widget GObjects; no profile lookup/widget/color/display/service/Settings GUI/hardware acceptance.','compile_exit':0,'stage_exit':0,'original_tests_registered':registered,'original_tests_executed':[],'original_display_suite_pending':True,'consumer':consumers,'artifacts':{str(p.relative_to(w/'compile')):hashlib.sha256(p.read_bytes()).hexdigest() for p in (w/'compile').rglob('*') if p.is_file() and not p.is_symlink() and p.open('rb').read(4)==b'\x7fELF'},'stage_sha256':{str(p.relative_to('/stage')):hashlib.sha256(p.read_bytes()).hexdigest() for p in Path('/stage').rglob('*') if p.is_file() and not p.is_symlink()}}
(w/'stage-results.json').write_text(json.dumps(r,indent=2)+'\n');s=os.statvfs('/build');assert s.f_bavail*s.f_frsize>=16*1024**3
PY
