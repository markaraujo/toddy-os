#!/bin/bash
# BLFS 13.1 Qt 6.11.2 module-only, offscreen B01 feasibility prerequisite.
# This does not qualify a graphical desktop or enable a display-server backend.
set -euo pipefail
[[ $(id -u) == 101 && -f /src/CMakeLists.txt && -d /stage ]]
cmake -S /src -B /build/compile -G Ninja \
    -DCMAKE_INSTALL_PREFIX=/usr -DCMAKE_INSTALL_LIBDIR=lib \
    -DCMAKE_BUILD_TYPE=Release -DCMAKE_SKIP_RPATH=ON \
    -DQT_BUILD_TESTS=OFF -DQT_BUILD_EXAMPLES=OFF -DQT_GENERATE_SBOM=OFF \
    -DINPUT_xcb=no -DINPUT_opengl=no -DFEATURE_vulkan=OFF \
    -DFEATURE_vnc=OFF -DFEATURE_sql=OFF -DFEATURE_printsupport=OFF \
    -DFEATURE_eglfs=OFF -DFEATURE_linuxfb=OFF \
    -DINPUT_freetype=qt -DINPUT_harfbuzz=qt \
    -DINPUT_openssl=linked -DINPUT_dbus=linked
cmake --build /build/compile --parallel 6
DESTDIR=/stage cmake --install /build/compile
test -s /stage/usr/lib/libQt6Widgets.so.6.11.2
test -s /stage/usr/plugins/platforms/libqoffscreen.so
find /stage/usr -name '*.prl' -exec sed -i '/^QMAKE_PRL_BUILD_DIR/d' {} +
