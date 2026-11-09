#!/bin/bash
set -euo pipefail
[[ $(id -u) == 101 && ! -e /build/compile ]]
mkdir /build/compile
cd /build/compile
/src/configure --prefix=/usr --disable-static
make -j4
make -j2 check > /build/original-tests.log 2>&1
make DESTDIR=/stage install
make -C doc/reference DESTDIR=/stage install-data-local
cat > /build/toddy-schema.asn <<'EOF'
Toddy DEFINITIONS EXPLICIT TAGS ::= BEGIN
Envelope ::= SEQUENCE { number INTEGER, enabled BOOLEAN }
END
EOF
LD_LIBRARY_PATH=/stage/usr/lib /stage/usr/bin/asn1Parser -o /build/toddy-asn1-tab.c -n toddy_asn1_tab /build/toddy-schema.asn > /build/native-parser.log 2>&1
cc /src/toddy-probe.c /build/toddy-asn1-tab.c -I/stage/usr/include -L/stage/usr/lib -ltasn1 -Wl,-rpath,/stage/usr/lib -o /build/native-probe
/build/native-probe > /build/native-consumer.json
python3 - <<'PY'
from pathlib import Path
import hashlib,json,re
p=Path('/build');tests=[]
for path in (p/'compile').rglob('*.trs'):
 text=path.read_text();m=re.search(r'^:test-result: (\S+)$',text,re.M);assert m and m[1] in ['PASS','SKIP','XFAIL']
 tests.append({'name':str(path.relative_to(p/'compile')),'result':m[1]})
assert tests and any(r['result']=='PASS' for r in tests)
result={'scope':'Original libtasn1 programs and strict DER typed/truncation/refusal/recovery C consumer; no PKCS11/trust-store/GNOME credential acceptance','compile_exit':0,'stage_exit':0,'original_tests':tests,'consumer':json.loads((p/'native-consumer.json').read_text()),'artifacts':{str(f.relative_to(p/'compile')):hashlib.sha256(f.read_bytes()).hexdigest() for f in (p/'compile').rglob('*') if f.is_file() and not f.is_symlink() and f.open('rb').read(4)==b'\x7fELF'},'stage_sha256':{str(f.relative_to(p/'stage')):hashlib.sha256(f.read_bytes()).hexdigest() for f in (p/'stage').rglob('*') if f.is_file() and not f.is_symlink()}}
(p/'stage-results.json').write_text(json.dumps(result,indent=2)+'\n')
PY
