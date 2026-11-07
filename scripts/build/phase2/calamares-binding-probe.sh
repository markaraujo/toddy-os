#!/bin/bash
# Probe the actual Calamares 3.4.3 bundled header/Python 3.14 boundary before Qt.
set -euo pipefail
[[ $(id -u) == 101 && -e /src/3rdparty/pybind11/include/pybind11/embed.h ]]
g++ -std=c++17 -O2 $(python3-config --includes) \
    -I/src/3rdparty/pybind11/include /src/toddy-binding-probe.cpp \
    $(python3-config --embed --ldflags) -o /stage/calamares-binding-probe
/stage/calamares-binding-probe
