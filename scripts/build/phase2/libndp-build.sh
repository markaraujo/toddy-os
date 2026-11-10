#!/bin/bash
set -euo pipefail
[[ $(id -u) == 101 && ! -e /build/compile ]]
export PYTHONDONTWRITEBYTECODE=1
mkdir /build/compile
cd /build/compile
/src/configure --prefix=/usr --sysconfdir=/etc --localstatedir=/var --disable-static
make -j4
make check > /build/original-check.log 2>&1
make DESTDIR=/stage install
cc /src/toddy-probe.c -I/stage/usr/include -L/stage/usr/lib -lndp -Wl,-rpath,/stage/usr/lib -o /build/native-probe
LD_LIBRARY_PATH=/stage/usr/lib /build/native-probe > /build/native-consumer.json
LD_LIBRARY_PATH=/stage/usr/lib /stage/usr/bin/ndptool --help > /build/CLI-help.log 2>&1
python3 - <<'PY'
from pathlib import Path
import hashlib,json
p=Path('/build');assert not list((p/'compile').rglob('*.trs')),'Review unexpected registered original tests'
r={'scope':'Frozen BLFS13.1 libndp1.9 for required NetworkManager dependency. Upstream has no test suite; make check exit0 is build plumbing only. Actual five NDP message types/wildcard refusal/payload clamp/lifecycle recovery C consumer, no packets, device/network/NetworkManager acceptance.','compile_exit':0,'stage_exit':0,'original_test_suite':'absent in frozen source/book; no test pass claimed','make_check_exit':0,'consumer':json.loads((p/'native-consumer.json').read_text()),'artifacts':{str(f.relative_to(p/'compile')):hashlib.sha256(f.read_bytes()).hexdigest() for f in (p/'compile').rglob('*') if f.is_file() and not f.is_symlink() and f.open('rb').read(4)==b'\x7fELF'},'stage_sha256':{str(f.relative_to(p/'stage')):hashlib.sha256(f.read_bytes()).hexdigest() for f in (p/'stage').rglob('*') if f.is_file() and not f.is_symlink()}}
(p/'stage-results.json').write_text(json.dumps(r,indent=2)+'\n')
PY
