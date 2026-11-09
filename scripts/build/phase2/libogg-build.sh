#!/bin/bash
set -euo pipefail
[[ $(id -u) == 101 && ! -e /build/compile ]]
mkdir /build/compile
cd /build/compile
/src/configure --prefix=/usr --libdir=/usr/lib --disable-static > /build/configure.log 2>&1
make -j4 > /build/compile.log 2>&1
make -j4 check > /build/upstream-tests.log 2>&1
make DESTDIR=/stage install > /build/stage.log 2>&1
cc -Wall -Wextra -Werror /src/toddy-probe.c -I/stage/usr/include \
    -L/stage/usr/lib -Wl,-rpath,/stage/usr/lib -logg -o /build/consumer
/build/consumer > /build/consumer.log 2>&1
python3 - <<'PY'
from pathlib import Path
import json
w=Path('/build');results=[]
for name in ['test_bitwise','test_framing']:
    path=w/('compile/src/'+name+'.trs')
    text=path.read_text();assert ':test-result: PASS' in text
    results.append({'name':name,'result':'PASS','exit':0})
(w/'test-results.json').write_text(json.dumps({
    'scope':'Native Ogg original bitpacking/framing and C packet/CRC APIs only; no decoded audio, device or desktop output acceptance',
    'upstream_drivers':results,'staged_consumer_exit':0,
    'profile':'Shared Ogg container library/headers/data; no new audio service or user configuration'
},indent=2)+'\n')
PY
