#!/bin/bash
set -euo pipefail
[[ $(id -u) == 101 && -d /stage ]]
ulimit -c 0
meson setup /build/compile /src --prefix=/usr --libdir=lib --buildtype=release \
    --default-library=shared --wrap-mode=nofallback -Ddocs=false -Dtests=true -Dbin=true
ninja -C /build/compile -j4
meson test -C /build/compile --print-errorlogs --num-processes 4
DESTDIR=/stage ninja -C /build/compile install
[[ -f /stage/usr/lib/libfribidi.so.0 && -f /stage/usr/bin/fribidi ]]
