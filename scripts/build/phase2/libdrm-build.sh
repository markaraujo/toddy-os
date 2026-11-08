#!/bin/bash
set -euo pipefail
[[ $(id -u) == 101 && ! -e /build/compile ]]
ulimit -c 0
meson setup /build/compile /src --prefix=/usr --libdir=lib --buildtype=release --wrap-mode=nofallback \
    -Dudev=true -Dvalgrind=disabled -Dman-pages=disabled -Dcairo-tests=disabled \
    -Dintel=enabled -Dradeon=enabled -Damdgpu=enabled -Dnouveau=enabled -Dvmwgfx=enabled \
    -Dtests=true -Dinstall-test-programs=false
ninja -C /build/compile -j4
meson test -C /build/compile --no-rebuild --print-errorlogs --num-processes 4
DESTDIR=/stage ninja -C /build/compile install
cc -Wall -Wextra -Werror /src/toddy-probe.c -I/stage/usr/include -I/stage/usr/include/libdrm \
    -L/stage/usr/lib $(PKG_CONFIG_PATH=/stage/usr/lib/pkgconfig pkg-config --cflags --libs libdrm) -o /build/consumer
LD_LIBRARY_PATH=/stage/usr/lib /build/consumer
python3 - <<'PY'
from pathlib import Path
import hashlib,json
p=Path('/build/compile/meson-logs/testlog.json');rows=[json.loads(line) for line in p.read_text().splitlines()]
assert rows and all((r['result']=='OK' and r['returncode']==0) or (r['result']=='SKIP' and r['returncode']==77) for r in rows)
Path('/build/test-results.json').write_text(json.dumps({'registered_upstream_tests':len(rows),'tests':[{'name':r['name'],'result':r['result'],'returncode':r['returncode']} for r in rows],'log_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'staged_consumer_exit':0,'scope':'Native memory/format APIs and invalid-FD denial; device suites may skip77 because private compiler namespace exposes no DRM devices'},indent=2)+'\n')
PY
