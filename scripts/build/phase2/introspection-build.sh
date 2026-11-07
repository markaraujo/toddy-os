#!/bin/bash
# BLFS 13.1 GI 1.86.0 scanner bootstrap; GLib owns its core GIR/typelib payload.
set -euo pipefail
[[ $(id -u) == 101 && -d /src/giscanner && -d /stage ]]
meson setup /build/compile /src --prefix=/usr --buildtype=release \
    --wrap-mode=nofallback -Ddoctool=disabled -Dgtk_doc=false -Dcairo=disabled \
    -Dbuild_introspection_data=false
ninja -C /build/compile -j8
meson test -C /build/compile --list > /build/test-list.txt
DESTDIR=/stage ninja -C /build/compile install
test -e /stage/usr/bin/g-ir-scanner
test -e /stage/usr/lib/libgirepository-1.0.so
