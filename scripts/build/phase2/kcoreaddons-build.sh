#!/bin/bash
set -euo pipefail
[[ $(id -u) == 101 && -d /src/src/lib ]]
cmake -S /src -B /build/compile -G Ninja \
    -DCMAKE_INSTALL_PREFIX=/usr -DCMAKE_INSTALL_LIBDIR=lib \
    -DCMAKE_BUILD_TYPE=Release -DCMAKE_SKIP_INSTALL_RPATH=ON \
    -DBUILD_SHARED_LIBS=ON -DBUILD_TESTING=OFF -DBUILD_PYTHON_BINDINGS=OFF \
    -DKCOREADDONS_USE_QML=OFF -DBUILD_QCH=OFF
cmake --build /build/compile --parallel 6
DESTDIR=/stage cmake --install /build/compile
test -s /stage/usr/lib/libKF6CoreAddons.so.6.29.0
