#!/bin/bash
# Frozen BLFS13.1 Pixman0.46.4 core, not optional GTK demos/PNG test tooling.
set -euo pipefail
[[ $(id -u) == 101 && -d /stage ]]
ulimit -c 0
meson setup /build/compile /src --prefix=/usr --libdir=lib --buildtype=release \
    --wrap-mode=nofallback -Dtests=enabled -Ddemos=disabled -Dgtk=disabled \
    -Dlibpng=disabled -Dopenmp=disabled
ninja -C /build/compile -j4
meson test -C /build/compile --print-errorlogs --num-processes 4
DESTDIR=/stage ninja -C /build/compile install
[[ -f /stage/usr/lib/libpixman-1.so.0 && -f /stage/usr/lib/pkgconfig/pixman-1.pc ]]
