#!/bin/bash
# Conditional B12 same-version QtBase rebuild; run only after retained inspection.
# Existing qualified isolated.sh provides read-only /src and unprivileged UID101.
set -euo pipefail
[[ $(id -u) == 101 && -f /src/.cmake.conf && -d /stage && ! -e /build/compile ]]
[[ -z $(find /stage -mindepth 1 -print -quit) ]]
[[ $(sed -n 's/^set(QT_REPO_MODULE_VERSION "\([^"]*\)").*/\1/p' /src/.cmake.conf) == 6.11.2 ]]
[[ $(pkg-config --modversion wayland-client wayland-cursor wayland-scanner | sort -u) == 1.26.0 ]]
[[ $(pkg-config --modversion xkbcommon) == 1.13.2 ]]
# Client QPA, shared-memory backing store and xdg-shell are IN qtbase6.11.2.
# No OpenGL, EGL/XCB, compositor, QtQuick or QtWayland archive is needed here.
cmake -S /src -B /build/compile -G Ninja \
    -DCMAKE_INSTALL_PREFIX=/usr -DCMAKE_INSTALL_LIBDIR=lib \
    -DCMAKE_BUILD_TYPE=Release -DCMAKE_SKIP_RPATH=OFF -DCMAKE_SKIP_INSTALL_RPATH=ON \
    -DQT_BUILD_TESTS=OFF -DQT_BUILD_EXAMPLES=OFF -DQT_GENERATE_SBOM=OFF \
    -DINPUT_xcb=no -DINPUT_opengl=no -DFEATURE_vulkan=OFF \
    -DFEATURE_vnc=OFF -DFEATURE_sql=OFF -DFEATURE_printsupport=OFF \
    -DFEATURE_eglfs=OFF -DFEATURE_linuxfb=OFF \
    -DFEATURE_wayland=ON -DFEATURE_waylandscanner=ON \
    -DFEATURE_wayland_client=ON -DFEATURE_wayland_client_xdg_shell=ON \
    -DFEATURE_xkbcommon=ON \
    -DINPUT_freetype=qt -DINPUT_harfbuzz=qt \
    -DINPUT_openssl=linked -DINPUT_dbus=linked
cmake --build /build/compile --parallel 6
DESTDIR=/stage cmake --install /build/compile
for file in usr/lib/libQt6Widgets.so.6.11.2 usr/lib/libQt6WaylandClient.so.6.11.2 \
    usr/plugins/platforms/libqwayland.so usr/plugins/wayland-shell-integration/libxdg-shell.so; do
    test -s "/stage/$file"
done
find /stage/usr -name '*.prl' -exec sed -i '/^QMAKE_PRL_BUILD_DIR/d' {} +
# Coordinator must run qt_wayland_inspect.py --stage --require, retain a verified
# manifest/notices, package ALL rebuilt qtbase files and qualify native upgrade.
# This script never promotes, installs or edits a running root.
