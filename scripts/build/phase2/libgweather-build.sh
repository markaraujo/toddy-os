#!/bin/bash
set -euo pipefail
[[ $(id -u) == 101 && ! -e /build/compile ]]
export PYTHONDONTWRITEBYTECODE=1 GSETTINGS_BACKEND=memory
meson setup /build/compile /src --prefix=/usr --libdir=lib --buildtype=release \
 --wrap-mode=nodownload -Denable_vala=false -Dgtk_doc=false -Dintrospection=true -Dtests=true -Dowm_apikey=
ninja -C /build/compile -j4
meson test -C /build/compile --print-errorlogs -j1 \
 test_libgweather duplicates timezones > /build/original-tests.log 2>&1
meson install -C /build/compile --destdir /stage --no-rebuild
cc /src/toddy-probe.c -I/stage/usr/include/libgweather-4.0 -L/stage/usr/lib \
 $(pkg-config --cflags --libs gio-2.0) -lgweather-4 -lm -Wl,-rpath,/stage/usr/lib -o /build/native-probe
LD_LIBRARY_PATH=/stage/usr/lib /build/native-probe > /build/native-consumer.json
python3 - <<'PY'
from pathlib import Path
import hashlib,json,re
p=Path('/build');tests=[json.loads(t) for t in (p/'compile/meson-logs/testlog.json').read_text().splitlines() if t.strip()]
core=[t for t in tests if t['name']!='libgweather:metar']
assert len(core)==3 and all(t['result']=='OK' and t['returncode']==0 for t in core)
external=[t for t in tests if t['name']=='libgweather:metar']
assert not external or (len(external)==1 and external[0]['result']=='ERROR' and external[0]['returncode']==-6 and 'aviationweather.gov' in external[0].get('stdout','')+external[0].get('stderr',''))
r={'scope':'Three selected original location/duplicates/timezone programs with nested skips preserved; external METAR program remains explicitly unqualified. Actual offline owned-data C lookup/variant/refusal/recovery; cancelled forecast-lifetime fixture in no-route namespace is not remote provider acceptance. Native stock schema/Info/GNOME integration pending.','compile_exit':0,'stage_exit':0,'selected_core_programs':3,'external_METAR_qualified':False,'original_tests':[{k:t[k] for k in ['name','result','returncode']}|{'nested_skip_lines':[line for line in t.get('stdout','').splitlines() if re.search(r'#\s*SKIP',line,re.I)]} for t in tests],'consumer':json.loads((p/'native-consumer.json').read_text()),'artifacts':{str(f.relative_to(p/'compile')):hashlib.sha256(f.read_bytes()).hexdigest() for f in (p/'compile').rglob('*') if f.is_file() and not f.is_symlink() and f.open('rb').read(4)==b'\x7fELF'},'stage_sha256':{str(f.relative_to(p/'stage')):hashlib.sha256(f.read_bytes()).hexdigest() for f in (p/'stage').rglob('*') if f.is_file() and not f.is_symlink()}}
(p/'stage-results.json').write_text(json.dumps(r,indent=2)+'\n')
PY
