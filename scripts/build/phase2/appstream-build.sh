#!/bin/bash
# Frozen AppStream1.1.6 core metadata bootstrap; no compose/Qt/APT integration.
set -euo pipefail
[[ $(id -u) == 101 && -f /src/meson.build && -d /stage ]]
meson setup /build/compile /src --prefix=/usr --libdir=lib --buildtype=release \
    --wrap-mode=nofallback -Dstemming=false -Dsystemd=false -Dcompose=false \
    -Dsvg-support=false -Dblake3-support=false -Dgir=true -Dtools=true -Dqt=false \
    -Ddisplay-detection=wayland -Dapt-support=false -Dbash-completion=false -Ddocs=false -Dapidocs=false \
    -Dinstall-docs=false -Dman=false
ninja -C /build/compile -j4
meson test -C /build/compile --num-processes 2 --print-errorlogs
DESTDIR=/stage ninja -C /build/compile install
export PKG_CONFIG_PATH=/stage/usr/lib/pkgconfig
cc /src/toddy-probe.c -I/stage/usr/include/appstream -o /build/native-metadata \
    -L/stage/usr/lib -Wl,-rpath,/stage/usr/lib $(pkg-config --cflags --libs appstream)
/build/native-metadata > /build/native-metadata.log 2>&1
GI_TYPELIB_PATH=/stage/usr/lib/girepository-1.0 LD_LIBRARY_PATH=/stage/usr/lib python3 -B - <<'GI' > /build/native-gi.log 2>&1
import gi
gi.require_version('AppStream','1.0')
from gi.repository import AppStream
c=AppStream.Component.new()
c.set_id('org.toddy.NativeProbe')
assert c.get_id()=='org.toddy.NativeProbe'
GI
python3 - <<'PY'
import json,re
from pathlib import Path
rows=[json.loads(l) for l in Path('/build/compile/meson-logs/testlog.json').read_text().splitlines() if l.strip()]
assert len(rows)==8 and all(r['result']=='OK' and r['returncode']==0 for r in rows)
summary=[]
for r in rows:
    lines=r.get('stdout','').splitlines()
    summary.append({'name':r['name'],'native_exit':r['returncode'],'passed_tap_cases':sum(bool(re.match(r'^ok\s+\d+',l)) and '# SKIP' not in l for l in lines),'skipped_tap_cases':[l for l in lines if '# SKIP' in l]})
Path('/build/test-results.json').write_text(json.dumps({'scope':'Native metadata core/API/GI bootstrap, not qualified application catalog or GUI','upstream_drivers':summary,'staged_consumer_exit':0,'gi_exit':0,'limitations':'Compose, stemming, systemd hooks, Qt, shell completions and Debian APT integration disabled in bootstrap profile'},indent=2)+'\n')
PY
