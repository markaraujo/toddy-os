#!/bin/bash
set -euo pipefail
[[ $(id -u) == 101 && ! -e /build/compile ]]
ulimit -c 0
export PYTHONDONTWRITEBYTECODE=1 LIBGL_ALWAYS_SOFTWARE=1 GALLIUM_DRIVER=llvmpipe EGL_PLATFORM=surfaceless XDG_CACHE_HOME=/build/cache
meson setup /build/compile /src --prefix=/usr --libdir=lib --buildtype=release --wrap-mode=nofallback \
    -Dglx=no -Degl=yes -Dx11=false -Ddocs=false -Dtests=true
ninja -C /build/compile -j4
meson test -C /build/compile --no-rebuild --print-errorlogs --num-processes 4
DESTDIR=/stage ninja -C /build/compile install
cc -Wall -Wextra -Werror /src/toddy-probe.c -I/stage/usr/include -L/stage/usr/lib \
    $(PKG_CONFIG_PATH=/stage/usr/lib/pkgconfig pkg-config --cflags --libs epoxy) -o /build/epoxy-consumer
LD_LIBRARY_PATH=/stage/usr/lib /build/epoxy-consumer > /build/native-render.log
python3 - <<'PY'
from pathlib import Path
import hashlib,json
p=Path('/build/compile/meson-logs/testlog.json');rows=[json.loads(line) for line in p.read_text().splitlines()]
assert len(rows)==4 and all(r['result']=='OK' and r['returncode']==0 for r in rows)
text=Path('/build/native-render.log').read_text();assert 'renderer: llvmpipe' in text
Path('/build/test-results.json').write_text(json.dumps({'scope':'Native Epoxy EGL/GLES dispatch, shaders/raster/pixel readback over owned Mesa, no window/physical/X11 acceptance',
    'registered_tests':4,'tests':[{'name':r['name'],'result':r['result'],'returncode':r['returncode']} for r in rows],
    'upstream_log_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'staged_consumer_exit':0,'native_render_stdout':text,
    'unregistered_tests':'Upstream EGL/GLX tests require X11. Current EGL-only profile registers four portable tests; independent real surfaceless EGL/GLES consumer required.'},indent=2)+'\n')
PY
