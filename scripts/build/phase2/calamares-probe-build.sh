#!/bin/bash
# B01 no-write native Calamares startup/Python-job target-plan feasibility only.
set -euo pipefail
[[ $(id -u) == 101 && -d /src/3rdparty/pybind11 && -d /src/toddy-fixtures ]]
skip=$(python3 - <<'PY'
from pathlib import Path
print(';'.join(sorted(p.name for p in Path('/src/src/modules').iterdir() if p.is_dir())))
PY
)
cmake -S /src -B /build/compile -G Ninja \
    -DCMAKE_INSTALL_PREFIX=/usr -DCMAKE_INSTALL_LIBDIR=lib \
    -DCMAKE_BUILD_TYPE=Release -DCMAKE_SKIP_INSTALL_RPATH=ON \
    -DWITH_QML=OFF -DWITH_PYTHON=ON -DWITH_PYBIND11=ON \
    -DINSTALL_POLKIT=OFF -DINSTALL_CONFIG=OFF -DBUILD_TESTING=OFF \
    -DBUILD_SCHEMA_TESTING=OFF -DBUILD_CRASH_REPORTING=OFF \
    -DSKIP_MODULES="$skip"
cmake --build /build/compile --parallel 6
DESTDIR=/stage cmake --install /build/compile
library=$(find /build/compile -name libcalamares.so -type l)
[[ -n $library && $library != *$'\n'* ]]
library_dir=$(dirname "$library")
c++ -std=c++17 /src/toddy-fixtures/calamares_probe.cpp \
    -I/src/src/libcalamares -I/build/compile/src/libcalamares \
    $(pkg-config --cflags --libs Qt6Widgets Qt6Svg Qt6Concurrent Qt6DBus Qt6Network) \
    -L"$library_dir" -lcalamares -o /build/calamares-no-write-probe
LD_LIBRARY_PATH="$library_dir" /build/calamares-no-write-probe
LD_LIBRARY_PATH=/stage/usr/lib QT_QPA_PLATFORM=offscreen /stage/usr/bin/calamares --version
