#!/bin/bash
set -euo pipefail
[[ $(id -u) == 101 && ! -e /build/compile && -d /src/toddy-test-sdk ]]
export PYTHONDONTWRITEBYTECODE=1
cmake -S /src -B /build/compile -G Ninja -DCMAKE_INSTALL_PREFIX=/usr \
 -DCMAKE_BUILD_TYPE=Release -DFASTFLOAT_TEST=OFF -DFASTFLOAT_BENCHMARKS=OFF
cmake --build /build/compile -j4
DESTDIR=/stage cmake --install /build/compile
# Separate test tree: never install the upstream private doctest framework.
cmake -S /src -B /build/tests -G Ninja -DCMAKE_INSTALL_PREFIX=/usr \
 -DCMAKE_BUILD_TYPE=Release -DFASTFLOAT_TEST=ON -DFASTFLOAT_BENCHMARKS=OFF \
 -DFASTFLOAT_SUPPLEMENTAL_TESTS=OFF -DFASTFLOAT_EXHAUSTIVE=OFF \
 -DFETCHCONTENT_SOURCE_DIR_DOCTEST=/src/toddy-test-sdk \
 -DFETCHCONTENT_FULLY_DISCONNECTED=ON -DDOCTEST_NO_INSTALL=ON
cmake --build /build/tests -j4
ctest --test-dir /build/tests --show-only=json-v1 > /build/original-registered-tests.json
set +e
ctest --test-dir /build/tests --output-on-failure -j2 --output-junit /build/original-tests.xml > /build/original-tests.log 2>&1
result=$?
set -e
printf '%s\n' "$result" > /build/original-tests.exit
[[ $result == 0 ]]
python3 /src/toddy-probe.py /stage/usr /build > /build/native-consumer.json
python3 - <<'PY'
from pathlib import Path
import hashlib,json,xml.etree.ElementTree as ET
p=Path('/build');cases=ET.parse(p/'original-tests.xml').getroot().findall('.//testcase')
assert cases and not any(c.find(k) is not None for c in cases for k in ['failure','error','skipped'])
r={'scope':'Frozen Fast_float8.2.10 header/CMake SDK only. Stage before separate original tests with immutable private doctest source/no network/no SDK installation. Optional network supplemental datasets and default-off exhaustive sweeps/benchmarks omitted; not passes. Actual staged CMake consumer float/double/integer-prefix/invalid/overflow/reset cases only; no VTE/terminal/UI acceptance.','compile_exit':0,'stage_exit':0,'original_tests':[{'name':c.get('name'),'status':c.get('status')} for c in cases],'consumer':json.loads((p/'native-consumer.json').read_text()),'artifacts':{str(f.relative_to(p/'tests')):hashlib.sha256(f.read_bytes()).hexdigest() for f in (p/'tests').rglob('*') if f.is_file() and not f.is_symlink() and f.open('rb').read(4)==b'\x7fELF'},'stage_sha256':{str(f.relative_to(p/'stage')):hashlib.sha256(f.read_bytes()).hexdigest() for f in (p/'stage').rglob('*') if f.is_file() and not f.is_symlink()}}
assert not any('doctest' in name for name in r['stage_sha256'])
(p/'stage-results.json').write_text(json.dumps(r,indent=2)+'\n')
PY
