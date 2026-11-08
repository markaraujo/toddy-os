#!/bin/bash
set -euo pipefail
[[ $(id -u) == 101 && -d /stage && -f /etc/fonts/fonts.conf ]]
ulimit -c 0
# Native installed config's XDG font directory points at read-only source fixtures.
# This supplies test fonts without putting any into the system/default desktop.
export XDG_DATA_HOME=/src/tests
meson setup /build/compile /src --prefix=/usr --libdir=lib --buildtype=release \
    --default-library=shared --wrap-mode=nofallback -Dfontconfig=enabled \
    -Dfreetype=enabled -Dcairo=enabled -Dxft=disabled -Dlibthai=disabled \
    -Dintrospection=enabled -Ddocumentation=false -Dman-pages=false \
    -Dbuild-testsuite=true -Dbuild-examples=false
ninja -C /build/compile -j4
meson test -C /build/compile --print-errorlogs --num-processes 4
DESTDIR=/stage ninja -C /build/compile install
[[ -f /stage/usr/lib/libpango-1.0.so.0 && -f /stage/usr/lib/girepository-1.0/PangoCairo-1.0.typelib ]]
