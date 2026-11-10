#!/bin/bash
set -euo pipefail
[[ $(id -u) == 101 && ! -e /build/compile ]]
export PYTHONDONTWRITEBYTECODE=1
ulimit -c 0
python3 - <<'PY'
import os
s=os.statvfs('/build');assert s.f_bavail*s.f_frsize>=256*1024**2
PY
cmake -S /src -B /build/compile -G Ninja -DCMAKE_INSTALL_PREFIX=/usr -DCMAKE_INSTALL_LIBDIR=lib -DCMAKE_BUILD_TYPE=Release -DCMAKE_SKIP_INSTALL_RPATH=ON -DBUILD_DOCUMENTATION=OFF
cmake --build /build/compile -j4 > /build/original-build.log 2>&1
ctest --test-dir /build/compile --output-on-failure --parallel 4 --timeout 60 --output-junit /build/original-tests.xml > /build/original-tests.log 2>&1
DESTDIR=/stage cmake --install /build/compile
LD_LIBRARY_PATH=/stage/usr/lib python3 /src/toddy-probe.py /stage /build/consumer > /build/native-consumer.json
python3 - <<'PY'
from pathlib import Path
import hashlib,json,os,xml.etree.ElementTree as ET
w=Path('/build');tests=ET.parse(w/'original-tests.xml').getroot().findall('.//testcase');assert tests and all(not any(t.find(k) is not None for k in ['failure','error','skipped']) for t in tests)
s=os.statvfs(w);assert s.f_bavail*s.f_frsize>=256*1024**2
r={'scope':'EditorConfig0.12.11 original exact test gitlink, shared C library/CLI with owned PCRE2; optional docs off. Layered UTF8 configuration/error/recovery C API+CLI, no graphical editor/security-wide claim.','compile_exit':0,'stage_exit':0,'original_ctest_cases':len(tests),'consumer':json.loads((w/'native-consumer.json').read_text()),'scratch_free_bytes':s.f_bavail*s.f_frsize,'artifacts':{str(p.relative_to(w/'compile')):hashlib.sha256(p.read_bytes()).hexdigest() for p in (w/'compile').rglob('*') if p.is_file() and not p.is_symlink() and p.open('rb').read(4)==b'\x7fELF'},'stage_sha256':{str(p.relative_to(w/'stage')):hashlib.sha256(p.read_bytes()).hexdigest() for p in (w/'stage').rglob('*') if p.is_file() and not p.is_symlink()}}
(w/'stage-results.json').write_text(json.dumps(r,indent=2)+'\n')
PY
