#!/bin/bash
# Frozen BLFS13.1 libxmlb0.3.29; GLib compressed XML query/GI dependency.
set -euo pipefail
[[ $(id -u) == 101 && -f /src/meson.build && -d /stage ]]
meson setup /build/compile /src --prefix=/usr --libdir=lib --buildtype=release \
    --wrap-mode=nofallback -Dgtkdoc=false -Dintrospection=true -Dtests=true \
    -Dstemmer=false -Dcli=true -Dlzma=enabled -Dzstd=enabled
ninja -C /build/compile -j4
meson test -C /build/compile --print-errorlogs
DESTDIR=/stage ninja -C /build/compile install
PKG_CONFIG_PATH=/stage/usr/lib/pkgconfig cc /src/toddy-probe.c \
    -I/stage/usr/include/libxmlb-2 -o /build/native-query \
    -L/stage/usr/lib -Wl,-rpath,/stage/usr/lib $(pkg-config --cflags --libs gio-2.0) -lxmlb
/build/native-query > /build/native-query.log 2>&1
GI_TYPELIB_PATH=/stage/usr/lib/girepository-1.0 LD_LIBRARY_PATH=/stage/usr/lib python3 - <<'GI' > /build/native-gi.log 2>&1
import gi
gi.require_version('Xmlb','2.0')
from gi.repository import Xmlb
silo=Xmlb.Silo.new_from_xml('<root><item>navy</item></root>')
assert silo.query_first('root/item').get_text()=='navy'
GI
python3 - <<'PY'
from pathlib import Path
import json,re
rows=[json.loads(l) for l in Path('/build/compile/meson-logs/testlog.json').read_text().splitlines() if l.strip()]
assert len(rows)==2 and all(r['result']=='OK' and r['returncode']==0 for r in rows)
summary=[]
for r in rows:
    lines=r.get('stdout','').splitlines()
    summary.append({'name':r['name'],'native_exit':r['returncode'],'passed_tap_cases':sum(bool(re.match(r'^ok\s+\d+',l)) and '# SKIP' not in l for l in lines),'skipped_tap_cases':[l for l in lines if '# SKIP' in l]})
Path('/build/test-results.json').write_text(json.dumps({'scope':'Native compressed XML query/API/GI dependency; no window acceptance','upstream_drivers':summary,'staged_consumer_exit':0,'gi_exit':0},indent=2)+'\n')
PY
