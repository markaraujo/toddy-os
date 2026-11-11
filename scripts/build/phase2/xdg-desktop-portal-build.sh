#!/bin/bash
set -euo pipefail
[[ $(id -u) == 101 && ! -e /build/compile ]]
export PYTHONDONTWRITEBYTECODE=1
ulimit -c 0
meson setup /build/compile /src --prefix=/usr --libdir=lib --buildtype=release \
 --wrap-mode=nofallback -Dtests=disabled -Dinstalled-tests=false \
 -Dsandboxed-image-validation=enabled -Dsandboxed-sound-validation=enabled \
 -Dsystemd=enabled -Dflatpak-interfaces=disabled -Dgeoclue=disabled -Dgudev=disabled \
 -Ddocumentation=disabled -Dman-pages=enabled
ninja -C /build/compile -j4
meson install -C /build/compile --destdir /stage --no-rebuild
python3 /src/toddy-build-result.py xdg-desktop-portal 1.22.1 usr/libexec/xdg-desktop-portal
