#!/bin/bash
set -euo pipefail
[[ $(id -u) == 101 && ! -e /build/compile ]]
export PYTHONDONTWRITEBYTECODE=1
cmake -S /src -B /build/compile -G Ninja -DCMAKE_INSTALL_PREFIX=/usr \
    -DLIB_INSTALL_DIR=/usr/lib -DCMAKE_BUILD_TYPE=Release \
    -DENABLE_TESTS=ON -DENABLE_INSTALLED_TESTS=OFF \
    -DENABLE_INTROSPECTION=ON -DENABLE_VALA_BINDINGS=OFF \
    -DENABLE_GTK_DOC=OFF -DENABLE_GI_DOCGEN=OFF -DENABLE_EXAMPLES=OFF \
    -DENABLE_GTK=ON -DENABLE_GTK4=ON -DENABLE_SMIME=ON \
    -DENABLE_OAUTH2_WEBKITGTK=OFF -DENABLE_OAUTH2_WEBKITGTK4=OFF \
    -DENABLE_GOA=OFF -DENABLE_WEATHER=OFF -DENABLE_CANBERRA=OFF \
    -DWITH_KRB5=OFF -DWITH_OPENLDAP=OFF -DWITH_SUNLDAP=OFF \
    -DWITH_PHONENUMBER=OFF -DWITH_LIBDB=OFF
cmake --build /build/compile -j4
ctest --test-dir /build/compile -j1 --output-on-failure \
    --output-junit /build/original-tests.xml > /build/original-tests.log 2>&1
DESTDIR=/stage cmake --install /build/compile
export PKG_CONFIG_PATH=/stage/usr/lib/pkgconfig
cc /src/toddy-probe.c -I/stage/usr/include/evolution-data-server \
    -L/stage/usr/lib $(pkg-config --cflags --libs libecal-2.0) \
    -Wl,-rpath,/stage/usr/lib -Wl,-rpath-link,/stage/usr/lib \
    -Wl,-rpath-link,/stage/usr/lib/evolution-data-server \
    -o /build/native-probe
LD_LIBRARY_PATH=/stage/usr/lib:/stage/usr/lib/evolution-data-server timeout 30s /build/native-probe > /build/native-consumer.json
python3 - <<'PY'
from pathlib import Path
import hashlib,json,xml.etree.ElementTree as ET
p=Path('/build');tests=[]
for case in ET.parse(p/'original-tests.xml').findall('.//testcase'):
    assert case.find('failure') is None and case.find('error') is None
    tests.append({'name':case.get('name'),'result':'SKIP' if case.find('skipped') is not None else 'PASS'})
assert tests
for name in ['test-cal-client-create-object','test-cal-client-modify-object','test-cal-client-remove-object','test-cal-component','libedataserver-test']:
    assert {'name':name,'result':'PASS'} in tests,name
result={'scope':'Enabled original EDS client/service/calendar/contact/private DBus/storage tests plus native UTF8/ICS/source identity/refusal/recovery. No real accounts, network providers, native desktop/login or graphical alarm acceptance.', 'compile_exit':0,'stage_exit':0,'original_tests':tests,'consumer':json.loads((p/'native-consumer.json').read_text()),'artifacts':{str(f.relative_to(p/'compile')):hashlib.sha256(f.read_bytes()).hexdigest() for f in (p/'compile').rglob('*') if f.is_file() and not f.is_symlink() and f.open('rb').read(4)==b'\x7fELF'},'stage_sha256':{str(f.relative_to(p/'stage')):hashlib.sha256(f.read_bytes()).hexdigest() for f in (p/'stage').rglob('*') if f.is_file() and not f.is_symlink()}}
(p/'stage-results.json').write_text(json.dumps(result,indent=2)+'\n')
PY
