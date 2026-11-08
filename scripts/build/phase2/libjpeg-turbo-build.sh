#!/bin/bash
set -euo pipefail
[[ $(id -u) == 101 && -d /stage ]]
ulimit -c 0
# Portable C backend; optional NASM/Yasm is absent. No native-CPU-only flags.
cmake -S /src -B /build/compile -G Ninja -DCMAKE_INSTALL_PREFIX=/usr \
    -DCMAKE_BUILD_TYPE=Release -DENABLE_STATIC=FALSE -DWITH_SIMD=OFF \
    -DCMAKE_INSTALL_DEFAULT_LIBDIR=lib -DCMAKE_SKIP_INSTALL_RPATH=ON \
    -DCMAKE_INSTALL_DOCDIR=/usr/share/doc/libjpeg-turbo-3.2.0
ninja -C /build/compile -j4
ctest --test-dir /build/compile --output-on-failure --output-junit /build/ctest.xml -j4
DESTDIR=/stage cmake --install /build/compile
[[ -f /stage/usr/lib/libjpeg.so && -f /stage/usr/lib/libturbojpeg.so ]]
