#!/bin/bash
set -euo pipefail
[[ $(id -u) == 101 && ! -e /build/compile ]]
mkdir /build/compile
cd /build/compile
/src/configure --prefix=/usr --disable-static --disable-openssl
make -j4
make -j2 check > /build/original-tests.log 2>&1
make DESTDIR=/stage install
chmod 755 /stage/usr/lib/libhogweed.so.* /stage/usr/lib/libnettle.so.*
cc /src/toddy-probe.c -I/stage/usr/include -L/stage/usr/lib -lhogweed -lnettle -lgmp -Wl,-rpath,/stage/usr/lib -o /build/native-probe
/build/native-probe > /build/native-consumer.json
python3 - <<'PY'
from pathlib import Path
import hashlib,json,re
p=Path('/build');text=(p/'original-tests.log').read_text();tests=[{'name':m[2],'result':m[1]} for m in re.finditer(r'^(PASS|SKIP|FAIL): (.+)$',text,re.M)]
assert tests and any(r['result']=='PASS' for r in tests) and not any(r['result']=='FAIL' for r in tests) and not re.search(r'\d+ of \d+ tests failed',text)
result={'scope':'Original Nettle/Hogweed crypto programs plus actual SHA256/P256 invalid-scalar/off-curve/refusal/recovery; no GnuTLS/TLS/remote network/GNOME acceptance','compile_exit':0,'stage_exit':0,'original_tests':tests,'consumer':json.loads((p/'native-consumer.json').read_text()),'artifacts':{str(f.relative_to(p/'compile')):hashlib.sha256(f.read_bytes()).hexdigest() for f in (p/'compile').rglob('*') if f.is_file() and not f.is_symlink() and f.open('rb').read(4)==b'\x7fELF'},'stage_sha256':{str(f.relative_to(p/'stage')):hashlib.sha256(f.read_bytes()).hexdigest() for f in (p/'stage').rglob('*') if f.is_file() and not f.is_symlink()}}
(p/'stage-results.json').write_text(json.dumps(result,indent=2)+'\n')
PY
