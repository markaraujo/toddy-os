#!/bin/bash
set -euo pipefail
[[ $(id -u) == 101 && ! -e /build/compile ]]
export PYTHONDONTWRITEBYTECODE=1
mkdir /build/compile
cd /build/compile
/src/configure --prefix=/usr --disable-static --disable-doc --disable-manpages \
    --disable-cxx --disable-libdane --disable-full-test-suite \
    --disable-valgrind-tests --without-tpm --without-tpm2 --without-leancrypto \
    --without-brotli --with-default-trust-store-pkcs11=pkcs11:
make -j4
# Standard original suite, including private protocol peers. This job must have
# the isolated loopback profile; no external route/provider/owner credentials.
make -j4 check > /build/original-tests.log 2>&1
make DESTDIR=/stage install
cc /src/toddy-probe.c -I/stage/usr/include -L/stage/usr/lib -lgnutls -Wl,-rpath,/stage/usr/lib -o /build/native-probe
/build/native-probe > /build/native-consumer.json
python3 - <<'PY'
from pathlib import Path
import hashlib,json,re
p=Path('/build');tests=[]
for path in (p/'compile').rglob('*.trs'):
 text=path.read_text();match=re.search(r'^:test-result: (\S+)$',text,re.M);assert match and match[1] in ['PASS','SKIP','XFAIL'];tests.append({'name':str(path.relative_to(p/'compile')),'result':match[1]})
assert tests and any(r['result']=='PASS' for r in tests)
for required in ['tests/tls13/supported_versions.trs','tests/tls13/anti_replay.trs']:
 assert {'name':required,'result':'PASS'} in tests,'Critical protocol/replay original unavailable'
result={'scope':'Standard original GnuTLS suite with isolated private-loopback peers plus actual crypto/UTF8/IDNA/priority/refusal/recovery consumer; full optional interop/fuzzer/Valgrind/FIPS/hardware/remote network/system trust/GNOME separate','compile_exit':0,'stage_exit':0,'original_tests':tests,'consumer':json.loads((p/'native-consumer.json').read_text()),'artifacts':{str(f.relative_to(p/'compile')):hashlib.sha256(f.read_bytes()).hexdigest() for f in (p/'compile').rglob('*') if f.is_file() and not f.is_symlink() and f.open('rb').read(4)==b'\x7fELF'},'stage_sha256':{str(f.relative_to(p/'stage')):hashlib.sha256(f.read_bytes()).hexdigest() for f in (p/'stage').rglob('*') if f.is_file() and not f.is_symlink()}}
(p/'stage-results.json').write_text(json.dumps(result,indent=2)+'\n')
PY
