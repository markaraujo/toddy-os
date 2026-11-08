#!/bin/bash
# Frozen libfyaml0.9.6, isolated native Check0.15.2 SDK for parser unit cases.
set -euo pipefail
[[ $(id -u) == 101 && -f /src/configure && -d /stage ]]
cmake -S /src/subprojects/check-0.15.2 -B /build/check-compile \
    -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_PREFIX=/build/test-sdk \
    -DCMAKE_INSTALL_LIBDIR=lib -DBUILD_TESTING=ON -DCHECK_ENABLE_TESTS=ON
cmake --build /build/check-compile -j4
ctest --test-dir /build/check-compile --output-on-failure --output-junit /build/check-ctest.xml
cmake --install /build/check-compile
export PKG_CONFIG_PATH=/build/test-sdk/lib/pkgconfig
export LD_LIBRARY_PATH=/build/test-sdk/lib
mkdir /build/compile
cd /build/compile
/src/configure --prefix=/usr --libdir=/usr/lib --disable-network \
    --disable-devmode --enable-portable-target --without-libclang
grep -q '^#define HAVE_COMPATIBLE_CHECK 1$' config.h
make -j4
make check > /build/upstream-check.log 2>&1
make DESTDIR=/stage install
export PKG_CONFIG_PATH=/stage/usr/lib/pkgconfig:/build/test-sdk/lib/pkgconfig
cc /src/toddy-probe.c \
    -I/stage/usr/include -o /build/native-yaml \
    -L/stage/usr/lib -Wl,-rpath,/stage/usr/lib $(pkg-config --cflags --libs libfyaml)
/build/native-yaml > /build/native-yaml.log 2>&1
python3 - <<'PY'
import json
from pathlib import Path
import xml.etree.ElementTree as ET
tests=ET.parse('/build/check-ctest.xml').getroot().findall('.//testcase')
assert tests and all(not any(c.find(t) is not None for t in ['failure','error','skipped']) for c in tests)
rows={}
for line in Path('/build/compile/test/test-suite.log').read_text().splitlines():
    if line.startswith('# ') and ':' in line:
        key,value=line[2:].split(':',1)
        if key in ['TOTAL','PASS','SKIP','XFAIL','FAIL','XPASS','ERROR']:rows[key]=int(value.strip())
assert rows['TOTAL']>0 and rows['TOTAL']==rows['PASS'] and all(rows.get(k,0)==0 for k in ['SKIP','XFAIL','FAIL','XPASS','ERROR'])
Path('/build/test-results.json').write_text(json.dumps({'scope':'Native portable YAML parser; private test SDK not runtime/catalog','check_sdk_ctest_cases':len(tests),'upstream_summary':rows,'staged_consumer_exit':0,'network_suites':'Explicitly disabled; no network in compiler sandbox','reflection':'Optional libclang reflection disabled'},indent=2)+'\n')
PY
