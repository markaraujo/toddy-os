#!/bin/bash
set -euo pipefail
[[ $(id -u) == 101 && -d /stage ]]
ulimit -c 0
meson setup /build/compile /src --prefix=/usr --libdir=lib --buildtype=release \
    --default-library=shared --wrap-mode=nodownload --force-fallback-for=mutest-1 -Dgtk_doc=false \
    -Dgobject_types=true -Dintrospection=enabled -Dtests=true -Dinstalled_tests=false
ninja -C /build/compile -j4
meson test -C /build/compile --print-errorlogs --num-processes 4
DESTDIR=/stage ninja -C /build/compile install
[[ -f /stage/usr/lib/libgraphene-1.0.so.0 && -f /stage/usr/lib/girepository-1.0/Graphene-1.0.typelib ]]
