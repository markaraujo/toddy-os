#!/bin/bash
set -euo pipefail
[[ $(id -u) == 101 && ! -e /build/compile ]]
mkdir /build/compile
cd /build/compile
/src/configure --prefix=/usr --libdir=/usr/lib --disable-static --enable-tests-build > /build/configure.log 2>&1
make -j4 > /build/compile.log 2>&1
make -C tests check TESTS='set_option init_context' > /build/upstream-tests.log 2>&1
make DESTDIR=/stage install > /build/stage.log 2>&1
cc -Wall -Wextra -Werror /src/toddy-probe.c -I/stage/usr/include/libusb-1.0 \
    -L/stage/usr/lib -Wl,-rpath,/stage/usr/lib -lusb-1.0 -o /build/consumer
/build/consumer > /build/consumer.log 2>&1
python3 - <<'PY'
from pathlib import Path
import json
w=Path('/build');rows=[]
for name in ['set_option','init_context']:
    text=(w/('compile/tests/'+name+'.trs')).read_text();assert ':test-result: PASS' in text
    rows.append({'name':name,'result':'PASS'})
(w/'test-results.json').write_text(json.dumps({'scope':'Native original libusb initialization/options drivers and no-device-discovery C lifecycle; no real USB hardware access','upstream_drivers':rows,'staged_consumer_exit':0,'omitted':'Unneeded 10000-iteration stress/stress_mt and unavailable umockdev hardware simulation are not passes; test logs preserve any original internal SKIP'},indent=2)+'\n')
PY
