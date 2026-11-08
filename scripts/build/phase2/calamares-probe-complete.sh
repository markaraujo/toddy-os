#!/bin/bash
# Resume the no-write consumer only; upstream compile/stage already completed.
set -euo pipefail
[[ $(id -u) == 101 && -e /build/compile/build.ninja && -x /stage/usr/bin/calamares ]]
library=$(find /build/compile -name libcalamares.so -type l)
[[ -n $library && $library != *$'\n'* ]]
library_dir=$(dirname "$library")
c++ -std=c++17 /src/toddy-fixtures/calamares_probe.cpp \
    -I/src/src/libcalamares -I/build/compile/src/libcalamares \
    $(pkg-config --cflags --libs Qt6Widgets Qt6Svg Qt6Concurrent Qt6DBus Qt6Network) \
    -L"$library_dir" -lcalamares -o /build/calamares-no-write-probe
LD_LIBRARY_PATH="$library_dir" /build/calamares-no-write-probe
LD_LIBRARY_PATH=/stage/usr/lib QT_QPA_PLATFORM=offscreen /stage/usr/bin/calamares --version
