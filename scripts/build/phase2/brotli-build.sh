#!/bin/bash
set -euo pipefail
[[ $(id -u) == 101 && ! -e /build/compile ]]
export PYTHONDONTWRITEBYTECODE=1
cmake -S /src -B /build/compile -G Ninja -DCMAKE_INSTALL_PREFIX=/usr -DCMAKE_INSTALL_LIBDIR=lib -DCMAKE_BUILD_TYPE=Release -DCMAKE_SKIP_INSTALL_RPATH=ON -DBUILD_SHARED_LIBS=ON -DBROTLI_DISABLE_TESTS=OFF -DBROTLI_BUILD_TOOLS=ON
ninja -C /build/compile -j4
ctest --test-dir /build/compile --show-only=json-v1 > /build/original-registered-tests.json
ctest --test-dir /build/compile --output-on-failure --output-junit /build/original-tests.xml -j4 > /build/original-tests.log 2>&1
printf '0\n' > /build/original-tests.exit
DESTDIR=/stage cmake --install /build/compile
LD_LIBRARY_PATH=/stage/usr/lib python3 /src/toddy-probe.py /stage/usr/bin/brotli /build/consumer > /build/native-consumer.json
python3 - <<'PY'
from pathlib import Path
import hashlib,json,xml.etree.ElementTree as E
w=Path('/build');cases=E.parse(w/'original-tests.xml').getroot().findall('.//testcase');assert cases and all(c.get('status')=='run' and c.find('failure') is None and c.find('skipped') is None for c in cases)
r={'scope':'Frozen Brotli1.2.0 shared encoder/decoder/common and CLI; original registered tarball-available C tests only. Optional external downloaded corpus and Python binding unselected, not passes. Own binary/UTF8/integrity/malformed/refusal/recovery only, no Exiv2/browser/GUI acceptance.','compile_exit':0,'stage_exit':0,'original_cases':[c.get('name') for c in cases],'consumer':json.loads((w/'native-consumer.json').read_text()),'artifacts':{str(p.relative_to(w/'compile')):hashlib.sha256(p.read_bytes()).hexdigest() for p in (w/'compile').rglob('*') if p.is_file() and not p.is_symlink() and p.open('rb').read(4)==b'\x7fELF'},'stage_sha256':{str(p.relative_to('/stage')):hashlib.sha256(p.read_bytes()).hexdigest() for p in Path('/stage').rglob('*') if p.is_file() and not p.is_symlink()}}
(w/'stage-results.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({k:v for k,v in r.items() if k not in ('artifacts','stage_sha256')}))
PY
