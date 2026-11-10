#!/bin/bash
set -euo pipefail
[[ $(id -u) == 101 && ! -e /build/compile ]]
export PYTHONDONTWRITEBYTECODE=1
ulimit -c 0
meson setup /build/compile /src --prefix=/usr --libdir=lib --buildtype=release --wrap-mode=nofallback -Dgtk_doc=false -Dintrospection=true -Denable_vala=true
ninja -C /build/compile -j4 > /build/original-build.log 2>&1
meson introspect /build/compile --tests > /build/original-registered-tests.json
python3 - <<'PY'
from pathlib import Path
import json
assert json.loads(Path('/build/original-registered-tests.json').read_text())==[], 'Qualify any registered original tests separately'
PY
meson install -C /build/compile --destdir /stage --no-rebuild
LD_LIBRARY_PATH=/stage/usr/lib /stage/usr/bin/gsound-play --help > /build/actual-help.log 2>&1
python3 - <<'PY'
from pathlib import Path
import hashlib,json,os
w=Path('/build');help=(w/'actual-help.log').read_text();assert '--backend' in help and '--file' in help
for relative in ['usr/lib/pkgconfig/gsound.pc','usr/lib/girepository-1.0/GSound-1.0.typelib','usr/share/vala/vapi/gsound.vapi']:assert (Path('/stage')/relative).is_file()
r={'scope':'Frozen GSound1.0.3 libcanberra GObject/GI/Vala wrapper and command-line help only; no original tests registered, NOT a suite pass. No sound device/speaker/notification/Bluetooth/Settings/GUI acceptance.','compile_exit':0,'stage_exit':0,'original_tests_registered':[],'no_registered_tests_not_a_pass':True,'consumer':{'help':help},'artifacts':{str(p.relative_to(w/'compile')):hashlib.sha256(p.read_bytes()).hexdigest() for p in (w/'compile').rglob('*') if p.is_file() and not p.is_symlink() and p.open('rb').read(4)==b'\x7fELF'},'stage_sha256':{str(p.relative_to('/stage')):hashlib.sha256(p.read_bytes()).hexdigest() for p in Path('/stage').rglob('*') if p.is_file() and not p.is_symlink()}}
(w/'stage-results.json').write_text(json.dumps(r,indent=2)+'\n');s=os.statvfs('/build');assert s.f_bavail*s.f_frsize>=16*1024**3
PY
