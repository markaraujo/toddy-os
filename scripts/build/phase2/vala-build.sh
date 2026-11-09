#!/bin/bash
set -euo pipefail
[[ $(id -u) == 101 && ! -e /build/compile ]]
export PYTHONDONTWRITEBYTECODE=1
mkdir /build/compile
cd /build/compile
CFLAGS='-O2 -std=gnu17' /src/configure --prefix=/usr --libdir=/usr/lib \
    --disable-static --disable-valadoc --disable-coverage \
    --disable-test-asan --disable-test-ubsan
make -j4
make -j4 check > /build/original-tests.log 2>&1
make DESTDIR=/stage install
LD_LIBRARY_PATH=/stage/usr/lib:/stage/usr/lib/vala-0.56 python3 /src/toddy-probe.py /stage /build/consumer > /build/native-consumer.json
python3 - <<'PY'
from pathlib import Path
import hashlib,json,re
p=Path('/build');tests=[]
for f in (p/'compile').rglob('*.trs'):
    m=re.search(r'^:test-result: (\S+)$',f.read_text(),re.M)
    assert m and m[1] in ['PASS','SKIP','XFAIL']
    tests.append({'name':str(f.relative_to(p/'compile')),'result':m[1]})
assert tests and sum(t['result']=='PASS' for t in tests)>1000
assert 'check-fastvapi' in (p/'compile/tests/fastvapi/Makefile').read_text()
result={'scope':'Original Vala compiler semantic/code-generation tests and auxiliary checks; actual GObject/UTF8/signal/typed error C-ABI generation, invalid-source refusal/recovery. Compiler-only SDK, not IBus/native input/desktop acceptance.', 'compile_exit':0,'stage_exit':0,'C_dialect':'GNU17 for source-generated C with owned GCC16; sanitizers/Valadoc/coverage not selected', 'original_tests':tests,'consumer':json.loads((p/'native-consumer.json').read_text()),'artifacts':{str(f.relative_to(p/'compile')):hashlib.sha256(f.read_bytes()).hexdigest() for f in (p/'compile').rglob('*') if f.is_file() and not f.is_symlink() and f.open('rb').read(4)==b'\x7fELF'},'stage_sha256':{str(f.relative_to(p/'stage')):hashlib.sha256(f.read_bytes()).hexdigest() for f in (p/'stage').rglob('*') if f.is_file() and not f.is_symlink()}}
(p/'stage-results.json').write_text(json.dumps(result,indent=2)+'\n')
PY
