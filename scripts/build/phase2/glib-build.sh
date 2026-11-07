#!/bin/bash
# BLFS 13.1-systemd GLib-2.88.3 bootstrap, inside isolated.sh only.
set -euo pipefail
[[ $(id -u) == 101 && -d /src/glib && -d /stage ]]
meson setup /build/compile /src --prefix=/usr --buildtype=release \
    --wrap-mode=nofallback -Dintrospection=disabled -Dglib_debug=disabled \
    -Dman-pages=disabled -Dsysprof=disabled -Ddocumentation=false
ninja -C /build/compile -j8
meson test -C /build/compile --list > /build/test-list.txt
DESTDIR=/stage ninja -C /build/compile install
test -e /stage/usr/lib/libgio-2.0.so
test -e /stage/usr/lib/libgirepository-2.0.so
