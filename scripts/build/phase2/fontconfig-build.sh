#!/bin/bash
# Native upstream Meson offline tests; XML consumer uses already owned libxml2.
set -euo pipefail
[[ $(id -u) == 101 && -d /stage ]]
ulimit -c 0
export FONTCONFIG_FILE=/build/test-fonts.conf
mkdir /build/font-cache
printf '%s\n' '<?xml version="1.0"?><!DOCTYPE fontconfig SYSTEM "fonts.dtd"><fontconfig><dir>/src/test</dir><cachedir>/build/font-cache</cachedir></fontconfig>' > "$FONTCONFIG_FILE"
meson setup /build/compile /src --prefix=/usr --libdir=lib --sysconfdir=/etc \
    --localstatedir=/var --buildtype=release --default-library=shared --wrap-mode=nofallback \
    -Dxml-backend=libxml2 -Ddoc=disabled -Dtests=enabled -Dtools=enabled \
    -Dtests-external-fonts=disabled -Dtests-bwrap=disabled -Dcache-build=disabled
ninja -C /build/compile -j4
meson test -C /build/compile --print-errorlogs --num-processes 4
DESTDIR=/stage ninja -C /build/compile install
[[ -f /stage/etc/fonts/fonts.conf && -f /stage/usr/lib/libfontconfig.so.1 ]]
