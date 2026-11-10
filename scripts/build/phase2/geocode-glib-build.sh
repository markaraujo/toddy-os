#!/bin/bash
set -euo pipefail
[[ $(id -u) == 101 && ! -e /build/compile ]]
export PYTHONDONTWRITEBYTECODE=1
meson setup /build/compile /src --prefix=/usr --libdir=lib --buildtype=release \
 --wrap-mode=nodownload -Dsoup2=false -Denable-introspection=true \
 -Denable-installed-tests=false -Denable-gtk-doc=false
ninja -C /build/compile -j4
meson test -C /build/compile --print-errorlogs -j1 'Geo URI' 'Test mock backend' > /build/original-tests.log 2>&1
G_TEST_SRCDIR=/src/geocode-glib/tests /build/compile/geocode-glib/tests/geocode-glib --tap \
 -p /geocode/distance -p /geocode/zero_distance -p /geocode/osm_type > /build/original-portable-API.log 2>&1
meson install -C /build/compile --destdir /stage --no-rebuild
cc /src/toddy-probe.c -I/stage/usr/include/geocode-glib-2.0 -L/stage/usr/lib \
 $(pkg-config --cflags --libs gio-2.0) -lgeocode-glib-2 -lm -Wl,-rpath,/stage/usr/lib -o /build/native-probe
LD_LIBRARY_PATH=/stage/usr/lib /build/native-probe > /build/native-consumer.json
python3 - <<'PY'
from pathlib import Path
import hashlib,json,re
p=Path('/build');tests=[json.loads(s) for s in (p/'compile/meson-logs/testlog.json').read_text().splitlines() if s.strip()]
assert len(tests)==2 and all(t['result']=='OK' and t['returncode']==0 for t in tests)
api=(p/'original-portable-API.log').read_text();assert len(re.findall(r'^ok \d+ ',api,re.M))==3 and not re.search(r'^not ok',api,re.M)
result={'scope':'Original Geo URI and mock-backend drivers plus three portable original API paths; UTF8/geo-URI/refusal/recovery C ABI. Foreign-locale JSON fixtures and remote geocoding/GNOME not qualified; no key/account/network required.','compile_exit':0,'stage_exit':0,'original_tests':[{k:t[k] for k in ['name','result','returncode']} for t in tests],'original_API_paths':['/geocode/distance','/geocode/zero_distance','/geocode/osm_type'],'original_API_passes':3,'consumer':json.loads((p/'native-consumer.json').read_text()),'artifacts':{str(f.relative_to(p/'compile')):hashlib.sha256(f.read_bytes()).hexdigest() for f in (p/'compile').rglob('*') if f.is_file() and not f.is_symlink() and f.open('rb').read(4)==b'\x7fELF'},'stage_sha256':{str(f.relative_to(p/'stage')):hashlib.sha256(f.read_bytes()).hexdigest() for f in (p/'stage').rglob('*') if f.is_file() and not f.is_symlink()}}
(p/'stage-results.json').write_text(json.dumps(result,indent=2)+'\n')
PY
