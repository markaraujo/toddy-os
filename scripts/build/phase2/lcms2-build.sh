#!/bin/bash
# Pinned native color management, upstream core tests and bounded ICC consumer.
set -euo pipefail
[[ $(id -u) == 101 && -f /src/meson.build && -d /stage ]]
meson setup /build/compile /src --prefix=/usr --libdir=lib --buildtype=release \
    --wrap-mode=nofallback -Dtests=enabled -Dutils=true -Djpeg=enabled \
    -Dtiff=enabled -Dfastfloat=false -Dthreaded=false
ninja -C /build/compile -j4
meson test -C /build/compile --no-rebuild --print-errorlogs
DESTDIR=/stage ninja -C /build/compile install
export PKG_CONFIG_PATH=/stage/usr/lib/pkgconfig
cc -std=c11 -Wall -Wextra -Werror /src/toddy-probe.c -I/stage/usr/include \
    -o /build/native-icc -L/stage/usr/lib -Wl,-rpath,/stage/usr/lib \
    $(pkg-config --cflags --libs lcms2)
/build/native-icc > /build/native-icc.log 2>&1
python3 - <<'PY'
from pathlib import Path
import json
rows=[json.loads(x) for x in Path('/build/compile/meson-logs/testlog.json').read_text().splitlines()]
assert len(rows)==1 and rows[0]['name'].split(':')[-1]=='testcms'
assert rows[0]['result']=='OK' and rows[0]['returncode']==0
Path('/build/test-results.json').write_text(json.dumps({'scope':'Native color-management core and ICC serialize/reopen/navy identity/refusal; not a display or physical color calibration',
'upstream_drivers':[{'name':r['name'],'native_exit':r['returncode']} for r in rows],
'staged_consumer_exit':0,'icc_roundtrip':True,'navy_identity_tolerance_per_channel':1,
'malformed_icc_refusal':True,'profile':'Core plus JPEG/TIFF utilities; optional GPL fastfloat/threaded plugin products disabled; upstream core plugin API tests retained'},indent=2)+'\n')
PY
