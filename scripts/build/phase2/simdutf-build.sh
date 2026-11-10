#!/bin/bash
set -euo pipefail
[[ $(id -u) == 101 && ! -e /build/compile ]]
export PYTHONDONTWRITEBYTECODE=1
ulimit -c 0
cmake -S /src -B /build/compile -G Ninja -DCMAKE_INSTALL_PREFIX=/usr \
 -DCMAKE_INSTALL_LIBDIR=lib -DCMAKE_BUILD_TYPE=Release -DBUILD_SHARED_LIBS=ON \
 -DSIMDUTF_TESTS=ON -DSIMDUTF_FAST_TESTS=OFF -DSIMDUTF_ALWAYS_INCLUDE_FALLBACK=ON \
 -DSIMDUTF_TOOLS=OFF -DSIMDUTF_TOOL_TESTS=OFF -DSIMDUTF_BENCHMARKS=OFF \
 -DSIMDUTF_FUZZERS=OFF -DSIMDUTF_INTERNAL_TESTS=OFF -DFETCHCONTENT_FULLY_DISCONNECTED=ON
cmake --build /build/compile -j4
ctest --test-dir /build/compile --show-only=json-v1 > /build/original-registered-tests.json
set +e
ctest --test-dir /build/compile --output-on-failure -j2 --output-junit /build/original-tests.xml > /build/original-tests.log 2>&1
result=$?
set -e
printf '%s\n' "$result" > /build/original-tests.exit
[[ $result == 0 ]]
DESTDIR=/stage cmake --install /build/compile
LD_LIBRARY_PATH=/stage/usr/lib python3 /src/toddy-probe.py /stage/usr /build > /build/native-consumer.json
python3 - <<'PY'
from pathlib import Path
import hashlib,json,xml.etree.ElementTree as ET
p=Path('/build');cases=ET.parse(p/'original-tests.xml').getroot().findall('.//testcase')
assert cases and not any(c.find(k) is not None for c in cases for k in ['failure','error','skipped'])
r={'scope':'Frozen simdutf9.0.0 shared/SDK library, full default Unicode/base64 original tests with fast-test reduction OFF. Explicit scalar fallback retained for portable x86_64 baseline; actual runtime dispatch only on identified VM CPU. Optional CLI/tools/benchmarks/fuzz/internal/atomic-base64 developer matrices omitted, not passes. Actual staged CMake/shared Unicode UTF8→UTF16→UTF8 roundtrip/invalid-overlong-surrogate refusal/two recovery cycles only; no VTE/terminal/UI/other-hardware acceptance.','compile_exit':0,'stage_exit':0,'original_tests':[{'name':c.get('name'),'status':c.get('status')} for c in cases],'consumer':json.loads((p/'native-consumer.json').read_text()),'artifacts':{str(f.relative_to(p/'compile')):hashlib.sha256(f.read_bytes()).hexdigest() for f in (p/'compile').rglob('*') if f.is_file() and not f.is_symlink() and f.open('rb').read(4)==b'\x7fELF'},'stage_sha256':{str(f.relative_to(p/'stage')):hashlib.sha256(f.read_bytes()).hexdigest() for f in (p/'stage').rglob('*') if f.is_file() and not f.is_symlink()}}
(p/'stage-results.json').write_text(json.dumps(r,indent=2)+'\n')
PY
