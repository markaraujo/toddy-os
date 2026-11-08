#!/bin/bash
set -euo pipefail
[[ $(id -u) == 101 && -d /src/include/yaml-cpp ]]
cmake -S /src -B /build/compile -G Ninja \
    -DCMAKE_INSTALL_PREFIX=/usr -DCMAKE_INSTALL_LIBDIR=lib \
    -DCMAKE_BUILD_TYPE=Release -DCMAKE_SKIP_INSTALL_RPATH=ON \
    -DYAML_BUILD_SHARED_LIBS=ON -DYAML_CPP_BUILD_TESTS=OFF \
    -DYAML_CPP_BUILD_TOOLS=OFF -DYAML_CPP_FORMAT_SOURCE=OFF \
    -DYAML_CPP_DISABLE_UNINSTALL=ON
cmake --build /build/compile --parallel 6
DESTDIR=/stage cmake --install /build/compile
test -s /stage/usr/lib/libyaml-cpp.so.0.9.0
