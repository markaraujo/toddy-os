#!/bin/bash
set -euo pipefail
[[ $(id -u) == 101 && ! -e /build/compile ]]
mkdir /build/compile
cd /build/compile
/src/configure --prefix=/usr --disable-static
make -j4
make -j4 check > /build/original-tests.log 2>&1
make DESTDIR=/stage install
cc /src/toddy-probe.c -I/stage/usr/include -L/stage/usr/lib -lidn2 -Wl,-rpath,/stage/usr/lib -o /build/native-probe
/build/native-probe > /build/native-consumer.json
python3 - <<'PY'
from pathlib import Path
import hashlib,json,re
p=Path('/build');tests=[]
for path in (p/'compile').rglob('*.trs'):
 text=path.read_text();match=re.search(r'^:test-result: (\S+)$',text,re.M);assert match and match[1] in ['PASS','SKIP','XFAIL'];tests.append({'name':str(path.relative_to(p/'compile')),'result':match[1]})
assert tests and any(r['result']=='PASS' for r in tests)
result={'scope':'Original IDNA programs and native UTF8/punycode/nontransitional/refusal/recovery; no actual DNS/TLS/remote network/GNOME acceptance','compile_exit':0,'stage_exit':0,'original_tests':tests,'consumer':json.loads((p/'native-consumer.json').read_text()),'artifacts':{str(f.relative_to(p/'compile')):hashlib.sha256(f.read_bytes()).hexdigest() for f in (p/'compile').rglob('*') if f.is_file() and not f.is_symlink() and f.open('rb').read(4)==b'\x7fELF'},'stage_sha256':{str(f.relative_to(p/'stage')):hashlib.sha256(f.read_bytes()).hexdigest() for f in (p/'stage').rglob('*') if f.is_file() and not f.is_symlink()}}
(p/'stage-results.json').write_text(json.dumps(result,indent=2)+'\n')
PY
