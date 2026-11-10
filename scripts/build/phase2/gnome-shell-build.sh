#!/bin/bash
set -euo pipefail
[[ $(id -u) == 101 && ! -e /build/compile ]]
export PYTHONDONTWRITEBYTECODE=1
ulimit -c 0
# Frozen BLFS bootstrap profile: display-bound upstream suite requires a real
# Wayland session and Mutter test SDK. It remains a later gate, never a pass here.
meson setup /build/compile /src --prefix=/usr --libdir=lib --sysconfdir=/etc \
 --localstatedir=/var --buildtype=release --wrap-mode=nodownload \
 -Dtests=false -Dgtk_doc=false -Dman=true -Dnetworkmanager=true -Dsystemd=true \
 -Dcamera_monitor=true -Dextensions_tool=false -Dextensions_app=false -Dportal_helper=false
ninja -C /build/compile -j4
meson introspect /build/compile --tests > /build/original-registered-tests.json
meson install -C /build/compile --destdir /stage --no-rebuild
export LD_LIBRARY_PATH=/stage/usr/lib/gnome-shell:/usr/lib/mutter-18
export GI_TYPELIB_PATH=/stage/usr/lib/gnome-shell:/usr/lib/mutter-18
/stage/usr/bin/gnome-shell --version > /build/shell-version.log 2>&1
python3 /src/toddy-probe.py /src /stage /build > /build/native-consumer.json
python3 - <<'PY'
from pathlib import Path
import hashlib,json
p=Path('/build');rows=json.loads((p/'original-registered-tests.json').read_text());assert rows==[]
assert (p/'shell-version.log').read_text().strip()=='GNOME Shell 50.4'
r={'scope':'Frozen minimal Wayland/Systemd/NM/PipeWire camera profile; extensions management tools/apps and built-in WebKit captive portal helper omitted. Upstream display suite not selected as required native Wayland session/Mutter test SDK are pending. Own actual GJS source params/refusal/recovery, staged CLI/GI and private schema memory checks only; no graphical/login/UI acceptance.','compile_exit':0,'stage_exit':0,'original_tests':rows,'original_suite_pending':True,'consumer':json.loads((p/'native-consumer.json').read_text()),'version':(p/'shell-version.log').read_text().strip(),'artifacts':{str(f.relative_to(p/'compile')):hashlib.sha256(f.read_bytes()).hexdigest() for f in (p/'compile').rglob('*') if f.is_file() and not f.is_symlink() and f.open('rb').read(4)==b'\x7fELF'},'stage_sha256':{str(f.relative_to(p/'stage')):hashlib.sha256(f.read_bytes()).hexdigest() for f in (p/'stage').rglob('*') if f.is_file() and not f.is_symlink()}}
(p/'stage-results.json').write_text(json.dumps(r,indent=2)+'\n')
PY
