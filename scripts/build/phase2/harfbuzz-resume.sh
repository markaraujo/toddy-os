#!/bin/bash
# Resume unchanged compiler objects after owned desktop GIR dependency installed.
set -euo pipefail
[[ $(id -u) == 101 && -d /build/compile && ! -e /stage/usr ]]
ulimit -c 0
mkdir /build/dependency-recovery
cp /build/compile/.ninja_log /build/dependency-recovery/original-ninja-log
python3 - <<'BEFORE'
from pathlib import Path
import hashlib,json
files=['libharfbuzz.so.0.61431.0','libharfbuzz-gobject.so.0.61431.0','libharfbuzz-subset.so.0.61431.0']
Path('/build/dependency-recovery/before.json').write_text(json.dumps({f:hashlib.sha256((Path('/build/compile/src')/f).read_bytes()).hexdigest() for f in files},indent=2)+'\n')
BEFORE
ninja -C /build/compile -j4
meson test -C /build/compile --print-errorlogs --num-processes 4
python3 - <<'AFTER'
from pathlib import Path
import hashlib,json
before=json.loads(Path('/build/dependency-recovery/before.json').read_text())
after={f:hashlib.sha256((Path('/build/compile/src')/f).read_bytes()).hexdigest() for f in before}
assert before==after,'Unexpected core library rebuild; review instead of claiming reuse'
Path('/build/dependency-recovery/qualified.json').write_text(json.dumps({'original_core_libraries_unchanged':True,'before':before,'after':after,'correction':'owned GI desktop declarative types installed; resume existing Ninja graph'},indent=2)+'\n')
AFTER
DESTDIR=/stage ninja -C /build/compile install
[[ -f /stage/usr/lib/libharfbuzz.so.0 && -f /stage/usr/lib/girepository-1.0/HarfBuzz-0.0.typelib ]]
