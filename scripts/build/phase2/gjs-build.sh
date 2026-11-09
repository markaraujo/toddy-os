#!/bin/bash
# Frozen BLFS13.1 GJS1.88.1; display-dependent JS suites remain a native gate.
set -euo pipefail
[[ $(id -u) == 101 && -f /src/meson.build && -d /stage ]]
meson setup /build/compile /src --prefix=/usr --libdir=lib --buildtype=release \
    --wrap-mode=nofallback -Dprofiler=disabled -Dinstalled_tests=false
ninja -C /build/compile -j4
meson test -C /build/compile --no-rebuild --print-errorlogs -j2 \
    'API tests' 'Internal API tests' > /build/original-api-tests.log 2>&1
printf '0\n' > /build/original-api-tests.exit
DESTDIR=/stage ninja -C /build/compile install
export PKG_CONFIG_PATH=/stage/usr/lib/pkgconfig
export GI_TYPELIB_PATH=/stage/usr/lib/gjs/girepository-1.0
export LD_LIBRARY_PATH=/stage/usr/lib
cc -Wall -Wextra -Werror /src/toddy-probe.c -o /build/native-consumer \
    -I/stage/usr/include/gjs-1.0 -L/stage/usr/lib -Wl,-rpath,/stage/usr/lib \
    $(pkg-config --cflags --libs gjs-1.0)
/build/native-consumer > /build/native-consumer.log 2>&1
python3 -B /src/toddy-probe.py
python3 - <<'PY'
from pathlib import Path
import json
rows=[json.loads(line) for line in Path('/build/compile/meson-logs/testlog.json').read_text().splitlines() if line.strip()]
assert len(rows)==2 and all(r['returncode']==0 and r['result']=='OK' for r in rows)
proof={'scope':'Native GJS C/internal API original drivers plus real C/CLI/GI/event/refusal/recovery; all display-dependent JS/native GNOME suites pending',
       'native_build_exit':0,'stage_exit':0,'original_api_drivers':[{k:r[k] for k in ['name','returncode','result']} for r in rows],
       'native_c_consumer_exit':0,'cli':json.loads(Path('/build/cli-probe-results.json').read_text()),
       'unqualified':'Display-dependent JS suites, actual GJS GTK windows and GNOME Shell remain pending before integration acceptance'}
Path('/build/stage-results.json').write_text(json.dumps(proof,indent=2)+'\n')
PY
