#!/bin/bash
# BLFS13.1 Wayland1.26.0 native libraries/scanner and all upstream tests.
set -euo pipefail
[[ $(id -u) == 101 && -d /stage ]]
ulimit -c 0
export XDG_RUNTIME_DIR=/build/runtime
mkdir -m700 "$XDG_RUNTIME_DIR"
meson setup /build/compile /src --prefix=/usr --libdir=lib --buildtype=release \
    --wrap-mode=nofallback -Ddocumentation=false -Dtests=true -Ddtd_validation=true
ninja -C /build/compile -j4
meson test -C /build/compile --print-errorlogs --num-processes 4
DESTDIR=/stage ninja -C /build/compile install
[[ -f /stage/usr/bin/wayland-scanner && -f /stage/usr/lib/libwayland-client.so.0 ]]
