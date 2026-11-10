#!/bin/bash
set -euo pipefail
[[ $(id -u) == 101 && ! -e /build/compile ]]
export PYTHONDONTWRITEBYTECODE=1
meson setup /build/compile /src --prefix=/usr --libdir=lib --buildtype=release --wrap-mode=nodownload
ninja -C /build/compile -j4
meson test -C /build/compile --print-errorlogs -j1 > /build/original-tests.log 2>&1
meson install -C /build/compile --destdir /stage --no-rebuild
python3 /src/toddy-probe.py /stage > /build/native-consumer.json
python3 - <<'PY'
from pathlib import Path
import hashlib,json
p=Path('/build');tests=[json.loads(s) for s in (p/'compile/meson-logs/testlog.json').read_text().splitlines() if s.strip()]
assert tests and all(t['result']=='OK' and t['returncode']==0 for t in tests)
assert (p/'stage/usr/share/gweather-locations/Locations.xml').read_bytes()==Path('/src/data/Locations.xml').read_bytes()
r={'scope':'Generated native-endian typed GVariant location database, registered original data/lint checks and actual source lookup/index invariants. Static pinned data, not owner location, remote forecasts or graphical GNOME acceptance.','compile_exit':0,'stage_exit':0,'original_tests':[{k:t[k] for k in ['name','result','returncode']} for t in tests],'consumer':json.loads((p/'native-consumer.json').read_text()),'source_XML_sha256':hashlib.sha256(Path('/src/data/Locations.xml').read_bytes()).hexdigest(),'stage_sha256':{str(f.relative_to(p/'stage')):hashlib.sha256(f.read_bytes()).hexdigest() for f in (p/'stage').rglob('*') if f.is_file() and not f.is_symlink()}}
(p/'stage-results.json').write_text(json.dumps(r,indent=2)+'\n')
PY
