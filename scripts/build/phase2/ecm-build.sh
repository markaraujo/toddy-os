#!/bin/bash
# Frozen BLFS 13.1-systemd corrections applied only to the derived source copy.
set -euo pipefail
[[ $(id -u) == 101 && -d /src/kde-modules ]]
test ! -e /build/source
cp -R --no-preserve=ownership /src /build/source
sed -i '/"lib64"/s/64//' /build/source/kde-modules/KDEInstallDirsCommon.cmake
sed -e '/PACKAGE_INIT/i set(SAVE_PACKAGE_PREFIX_DIR "${PACKAGE_PREFIX_DIR}")' \
    -e '/^include/a set(PACKAGE_PREFIX_DIR "${SAVE_PACKAGE_PREFIX_DIR}")' \
    -i /build/source/ECMConfig.cmake.in
cmake -S /build/source -B /build/compile -G Ninja \
    -DCMAKE_INSTALL_PREFIX=/usr -DBUILD_WITH_QT6=ON \
    -DBUILD_DOC=OFF -DBUILD_TESTING=OFF
cmake --build /build/compile --parallel 6
DESTDIR=/stage cmake --install /build/compile
test -s /stage/usr/share/ECM/cmake/ECMConfig.cmake
