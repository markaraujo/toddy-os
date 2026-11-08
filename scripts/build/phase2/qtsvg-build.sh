#!/bin/bash
set -euo pipefail
[[ $(id -u) == 101 && -d /src/src/svg ]]
cmake -S /src -B /build/compile -G Ninja \
    -DCMAKE_INSTALL_PREFIX=/usr -DCMAKE_INSTALL_LIBDIR=lib \
    -DCMAKE_BUILD_TYPE=Release -DCMAKE_SKIP_INSTALL_RPATH=ON \
    -DQT_BUILD_TESTS=OFF -DQT_BUILD_EXAMPLES=OFF -DQT_GENERATE_SBOM=OFF
cmake --build /build/compile --parallel 6
DESTDIR=/stage cmake --install /build/compile
test -s /stage/usr/lib/libQt6Svg.so.6.11.2
find /stage/usr -name '*.prl' -exec sed -i '/^QMAKE_PRL_BUILD_DIR/d' {} +
