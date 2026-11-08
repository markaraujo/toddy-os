#!/bin/bash
# BLFS13.1 Wayland-Protocols1.49 with the already qualified native scanner.
set -euo pipefail
[[ $(id -u) == 101 && -d /stage ]]
meson setup /build/compile /src --prefix=/usr --libdir=lib --buildtype=release \
    --wrap-mode=nofallback -Dtests=true
ninja -C /build/compile -j4
meson test -C /build/compile --print-errorlogs --num-processes 4
DESTDIR=/stage ninja -C /build/compile install
[[ -f /stage/usr/share/wayland-protocols/stable/xdg-shell/xdg-shell.xml ]]
