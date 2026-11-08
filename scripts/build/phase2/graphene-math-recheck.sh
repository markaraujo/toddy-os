#!/bin/bash
# Authenticated archive already bundles MuTest. Enable only that local fallback.
set -euo pipefail
[[ $(id -u) == 101 && -f /src/subprojects/mutest/meson.build ]]
ulimit -c 0
mkdir /build/math-qualification
cp /build/compile/meson-logs/testlog.json /build/math-qualification/original-introspection.json
python3 - <<'BEFORE'
from pathlib import Path
import hashlib,json
paths=[p for p in Path('/build/compile/src').glob('lib*.so.*') if p.is_file() and not p.is_symlink()]
assert paths
Path('/build/math-qualification/before.json').write_text(json.dumps({str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},indent=2)+'\n')
BEFORE
meson configure /build/compile -Dwrap_mode=nodownload -Dforce_fallback_for=mutest-1
ninja -C /build/compile -j4
# Only the newly available CPU math drivers; prior GI driver remains unchanged.
meson test -C /build/compile --no-rebuild --print-errorlogs --num-processes 4 \
    box euler frustum matrix plane point point3d quad quaternion ray rect simd size \
    sphere triangle vec2 vec3 vec4
python3 - <<'AFTER'
from pathlib import Path
import hashlib,json
base=Path('/build/math-qualification');before=json.loads((base/'before.json').read_text());after={p:hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in before};assert before==after
rows=[json.loads(l) for l in Path('/build/compile/meson-logs/testlog.json').read_text().splitlines()]
assert len(rows)==18 and all(r['result']=='OK' and r['returncode']==0 for r in rows)
(base/'qualified.json').write_text(json.dumps({'prior_shared_libraries_unchanged':True,'before':before,'after':after,'new_math_drivers':18,'dependency':'original archive bundled MIT MuTest2019.1; nodownload local fallback only','prior_introspection_driver_reused':1},indent=2)+'\n')
AFTER
