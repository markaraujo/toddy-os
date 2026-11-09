#!/bin/bash
set -euo pipefail
[[ $(id -u) == 101 && ! -e /build/compile ]]
meson setup /build/compile /src --prefix=/usr --libdir=lib --buildtype=release \
    --wrap-mode=nofallback -Dtests=true -Dumockdev=disabled -Dvapi=false \
    -Ddocs=false -Dintrospection=true > /build/configure.log 2>&1
ninja -C /build/compile -j4 > /build/compile.log 2>&1
ninja -C /build/compile gusb/libgusb.ver > /build/api-map.log 2>&1
meson test -C /build/compile --no-rebuild --print-errorlogs gusb-exported-api > /build/upstream-tests.log 2>&1
/build/compile/gusb/gusb-self-test -p '/gusb/context{lookup}' > /build/original-lookup.log 2>&1
/build/compile/gusb/gusb-self-test -p '/gusb/device[json]' > /build/original-json.log 2>&1
DESTDIR=/stage meson install -C /build/compile --no-rebuild > /build/stage.log 2>&1
cc -Wall -Wextra -Werror /src/toddy-probe.c -I/stage/usr/include/gusb-1 \
    -L/stage/usr/lib -Wl,-rpath,/stage/usr/lib \
    $(pkg-config --cflags --libs gio-2.0 json-glib-1.0 libusb-1.0) -lgusb -o /build/consumer
/build/consumer > /build/consumer.log 2>&1
python3 - <<'PY'
from pathlib import Path
import json
w=Path('/build');rows=[json.loads(s) for s in (w/'compile/meson-logs/testlog.json').read_text().splitlines() if s.strip()]
assert len(rows)==1 and rows[0]['result']=='OK' and rows[0]['returncode']==0
for name,test in [('lookup','/gusb/context{lookup}'),('json','/gusb/device[json]')]:
    text=(w/('original-'+name+'.log')).read_text();assert 'ok 1 '+test in text and '# SKIP' not in text
(w/'test-results.json').write_text(json.dumps({'scope':'Native GUsb exported API map, original USB ID lookup and JSON event replay fixtures plus own context/refusal APIs; no physical USB access','exported_api_exit':0,'original_portable_cases':2,'staged_consumer_exit':0,'omitted':'Physical devices/context enumeration requiring devices and unavailable umockdev tests not selected; JSON replay is a fixture, not hardware acceptance'},indent=2)+'\n')
PY
