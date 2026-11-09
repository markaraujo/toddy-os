#!/bin/bash
set -euo pipefail
[[ $(id -u) == 101 && ! -e /build/compile ]]
export PYTHONDONTWRITEBYTECODE=1
cmake -S /src -B /build/compile -G Ninja -DCMAKE_INSTALL_PREFIX=/usr \
    -DCMAKE_INSTALL_LIBDIR=lib -DCMAKE_BUILD_TYPE=Release \
    -DLIBICAL_STATIC=OFF -DLIBICAL_BUILD_DOCS=OFF -DLIBICAL_GLIB_BUILD_DOCS=OFF \
    -DLIBICAL_GLIB_VAPI=OFF -DLIBICAL_JAVA_BINDINGS=OFF \
    -DLIBICAL_GLIB=ON -DLIBICAL_GOBJECT_INTROSPECTION=ON \
    -DLIBICAL_BUILD_TESTING=ON -DLIBICAL_BUILD_TESTING_BIGFUZZ=OFF
cmake --build /build/compile -j2
ctest --test-dir /build/compile -j2 --output-on-failure -E '^recur$' --output-junit /build/original-tests.xml > /build/original-tests.log 2>&1
# icalfileset_new requires a writable lock; keep frozen source read-only.
cp /src/test-data/recur.txt /build/recur-private.txt
chmod 600 /build/recur-private.txt
/build/compile/src/test/recur /build/recur-private.txt > /build/original-recur.log 2>&1
cmp /src/test-data/recur.txt /build/recur-private.txt
rm /build/recur-private.txt
DESTDIR=/stage cmake --install /build/compile
cc /src/toddy-probe.c -I/stage/usr/include -L/stage/usr/lib -lical -Wl,-rpath,/stage/usr/lib -o /build/native-probe
/build/native-probe > /build/native-consumer.json
python3 - <<'PY'
from pathlib import Path
import hashlib,json,xml.etree.ElementTree as ET
p=Path('/build');tree=ET.parse(p/'original-tests.xml');tests=[]
for case in tree.findall('.//testcase'):
 assert case.find('failure') is None and case.find('error') is None
 tests.append({'name':case.get('name'),'result':'SKIP' if case.find('skipped') is not None else 'PASS'})
assert len(tests)==65 and all(r['result']=='PASS' for r in tests)
tests.append({'name':'recur-private-identical-file','result':'PASS'})
result={'scope':'Original libical/C++/GI calendar tests and native UTF8/UTC recurrence/refusal/recovery; no EDS/calendar UI/network acceptance','compile_exit':0,'stage_exit':0,'original_tests':tests,'consumer':json.loads((p/'native-consumer.json').read_text()),'artifacts':{str(f.relative_to(p/'compile')):hashlib.sha256(f.read_bytes()).hexdigest() for f in (p/'compile').rglob('*') if f.is_file() and not f.is_symlink() and f.open('rb').read(4)==b'\x7fELF'},'stage_sha256':{str(f.relative_to(p/'stage')):hashlib.sha256(f.read_bytes()).hexdigest() for f in (p/'stage').rglob('*') if f.is_file() and not f.is_symlink()}}
(p/'stage-results.json').write_text(json.dumps(result,indent=2)+'\n')
PY
