#!/bin/bash
# Conditional B12 same-version QtBase rebuild; run only after retained inspection.
# Existing qualified isolated.sh provides read-only /src and unprivileged UID101.
set -euo pipefail
[[ $(id -u) == 101 && -f /src/.cmake.conf && -d /stage && ! -e /build/compile ]]
[[ -z $(find /stage -mindepth 1 -print -quit) ]]
# Bounded compiler parallelism; no overlapping package/root transactions.
jobs=$(python3 - <<'BUILD_BUDGET'
import json,os
from pathlib import Path
values={line.split(':',1)[0]:line.split(':',1)[1].strip().split()[0] for line in Path('/proc/meminfo').read_text().splitlines()}
available=int(values['MemAvailable'])//1024
per_job=1024
jobs=min(8,len(os.sched_getaffinity(0)),max(0,(available-2048)//per_job))
if jobs<1:raise SystemExit('Insufficient build RAM reserve')
Path('/build/build-budget.json').write_text(json.dumps({'jobs':jobs,'available_mib':available,'reserve_mib':2048,'per_job_mib':per_job},sort_keys=True)+'\n')
print(jobs)
BUILD_BUDGET
)
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
    -DFEATURE_xkbcommon=ON -DFEATURE_fontconfig=ON \
    -DFEATURE_gtk3=OFF -DFEATURE_xlib=OFF -DFEATURE_icu=OFF -DFEATURE_sessionmanager=OFF \
    -DFEATURE_libproxy=OFF -DFEATURE_gssapi=OFF -DFEATURE_brotli=OFF \
    -DFEATURE_libinput=OFF -DFEATURE_mtdev=OFF -DFEATURE_tslib=OFF \
    -DINPUT_freetype=qt -DINPUT_harfbuzz=qt \
    -DINPUT_openssl=linked -DINPUT_dbus=linked
cmake --build /build/compile --parallel "$jobs"
DESTDIR=/stage cmake --install /build/compile
for file in usr/lib/libQt6Widgets.so.6.11.2 usr/lib/libQt6WaylandClient.so.6.11.2 \
    usr/plugins/platforms/libqwayland.so usr/plugins/wayland-shell-integration/libxdg-shell.so; do
    test -s "/stage/$file"
done
find /stage/usr -name '*.prl' -exec sed -i '/^QMAKE_PRL_BUILD_DIR/d' {} +
# Coordinator must run qt_wayland_inspect.py --stage --require, retain a verified
# manifest/notices, package ALL rebuilt qtbase files and qualify native upgrade.
# This script never promotes, installs or edits a running root.

# Private staged consumer uses staged headers first; the feature static_assert
# would fail against the installed old offscreen-only Gui headers.
python3 /src/toddy-qt-inspect.py /stage --stage --require > /build/qt-static-stage.json
c++ -std=c++17 -DTODDY_STAGED_QT /src/toddy-qt-probe.cpp \
    -I/stage/usr/include -I/stage/usr/include/QtCore -I/stage/usr/include/QtGui \
    -I/stage/usr/include/QtWidgets -I/stage/usr/include/QtNetwork \
    -I/stage/usr/include/QtDBus -I/stage/usr/include/QtConcurrent -L/stage/usr/lib \
    $(pkg-config --cflags --libs Qt6Widgets Qt6Network Qt6DBus Qt6Concurrent Qt6Svg) \
    -o /build/qt-staged-consumer
LD_LIBRARY_PATH=/stage/usr/lib QT_QPA_PLATFORM=offscreen QT_PLUGIN_PATH=/stage/usr/plugins \
    dbus-run-session -- /build/qt-staged-consumer > /build/qt-staged-consumer.log
LD_LIBRARY_PATH=/stage/usr/lib /usr/bin/lrelease -version > /build/qt-existing-lrelease.log 2>&1
python3 - <<'RESULT'
from pathlib import Path
import hashlib,json,os
assert os.getuid()==101
static=json.loads(Path('/build/qt-static-stage.json').read_text())
assert not static['qtbase_rebuild_required']
assert Path('/build/qt-staged-consumer.log').read_text().strip()=='QT6112_WIDGET_TLS_DBUS_CONCURRENT_EXISTING_SVG_WAYLAND_METADATA_PASSED'
assert '6.11.2' in Path('/build/qt-existing-lrelease.log').read_text()
Path('/build/qt-qualified.json').write_text(json.dumps({'version':1,'uid':os.getuid(),
    'stage_manifest_sha256':static['stage_manifest_sha256'],'staged_consumer_exit':0,
    'existing_lrelease_exit':0,'probe_sha256':hashlib.sha256(Path('/src/toddy-qt-probe.cpp').read_bytes()).hexdigest(),
    'scope':'Native staged offscreen/ELF metadata and existing Svg/Linguist compatibility; actual Wayland/root Calamares launch pending'},indent=2)+'\n')
RESULT
