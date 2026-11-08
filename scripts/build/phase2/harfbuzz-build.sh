#!/bin/bash
# Selected text shaping/GTK bindings; Cairo renders the UI, no optional HB GPU.
set -euo pipefail
[[ $(id -u) == 101 && -d /stage ]]
ulimit -c 0
meson setup /build/compile /src --prefix=/usr --libdir=lib --buildtype=release \
    --default-library=shared --wrap-mode=nofallback -Dtests=enabled \
    -Dfreetype=enabled -Dglib=enabled -Dgobject=enabled -Dintrospection=enabled \
    -Dcairo=disabled -Dchafa=disabled -Dpng=disabled -Dzlib=enabled \
    -Dicu=disabled -Dgraphite2=disabled -Ddocs=disabled \
    -Dgpu=disabled -Dgpu_demo=disabled -Draster=disabled -Dvector=disabled
ninja -C /build/compile -j4
meson test -C /build/compile --print-errorlogs --num-processes 4
DESTDIR=/stage ninja -C /build/compile install
[[ -f /stage/usr/lib/libharfbuzz.so.0 && -f /stage/usr/lib/girepository-1.0/HarfBuzz-0.0.typelib ]]
