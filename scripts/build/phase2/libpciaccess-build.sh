#!/bin/bash
set -euo pipefail
[[ $(id -u) == 101 && ! -e /build/compile ]]
ulimit -c 0
meson setup /build/compile /src --prefix=/usr --libdir=lib --buildtype=release --wrap-mode=nofallback \
    -Dlinux-rom-fallback=false -Dinstall-scanpci=false -Dzlib=enabled
ninja -C /build/compile -j4
meson test -C /build/compile --no-rebuild --print-errorlogs
DESTDIR=/stage ninja -C /build/compile install
cc -Wall -Wextra -Werror /src/toddy-probe.c -I/stage/usr/include -L/stage/usr/lib \
    $(PKG_CONFIG_PATH=/stage/usr/lib/pkgconfig pkg-config --cflags --libs pciaccess) -o /build/consumer
LD_LIBRARY_PATH=/stage/usr/lib /build/consumer
python3 - <<'PY'
from pathlib import Path
import json
Path('/build/test-results.json').write_text(json.dumps({'registered_upstream_tests':0,'upstream_suite':'Not provided by this source Meson recipe; empty target is not test acceptance','staged_consumer_exit':0,'scope':'Native unknown-ID API and cleanup only, no hardware enumeration/device write'})+'\n')
PY
