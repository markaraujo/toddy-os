#!/bin/bash
set -euo pipefail
[[ $(id -u) == 101 && -d /src/src/linguist ]]
# Only the release/translation tools required by Calamares, not Designer,
# Assistant, Clang, documentation, WebEngine or QML.
cmake -S /src -B /build/compile -G Ninja \
    -DCMAKE_INSTALL_PREFIX=/usr -DCMAKE_INSTALL_LIBDIR=lib \
    -DCMAKE_BUILD_TYPE=Release -DCMAKE_SKIP_INSTALL_RPATH=ON \
    -DQT_BUILD_TESTS=OFF -DQT_BUILD_EXAMPLES=OFF -DQT_GENERATE_SBOM=OFF \
    -DFEATURE_linguist=ON -DFEATURE_designer=OFF -DFEATURE_assistant=OFF \
    -DFEATURE_qdoc=OFF -DFEATURE_qdbus=OFF -DFEATURE_qtdiag=OFF \
    -DFEATURE_qtplugininfo=OFF -DFEATURE_pixeltool=OFF -DFEATURE_qtattributionsscanner=OFF \
    -DFEATURE_distancefieldgenerator=OFF -DFEATURE_kmap2qmap=OFF -DFEATURE_qev=OFF
cmake --build /build/compile --parallel 6
DESTDIR=/stage cmake --install /build/compile
test -x /stage/usr/bin/lrelease
