#!/bin/bash
# BLFS13.1 FreeType2.14.3: immutable book edits; dynamic HarfBuzz breaks cycle.
set -euo pipefail
[[ $(id -u) == 101 && -d /stage ]]
mkdir /build/compile
cd /build/compile
/src/configure --prefix=/usr --disable-static --enable-freetype-config \
    --with-harfbuzz=dynamic --with-zlib=yes --with-bzip2=yes --with-png=yes --with-brotli=no
make -j4
make DESTDIR=/stage install
cc /src/toddy-probe.c -I/stage/usr/include/freetype2 -L/stage/usr/lib \
   -Wl,-rpath,/stage/usr/lib -lfreetype -o /build/probe
/build/probe
printf '%s\n' '{"upstream_suite":"not provided","staged_consumer_exit":0,"scope":"version and authored BDF glyph bytes; not a default desktop font"}' > /build/test-results.json
[[ -f /stage/usr/lib/libfreetype.so.6 && -f /stage/usr/lib/pkgconfig/freetype2.pc ]]
