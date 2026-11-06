#!/bin/bash
# Frozen BLFS 13.1-systemd recipe with ADR-0017/0021 pinned additions.
set -euo pipefail
cd /sources/cmake-4.4.2
test ! -e /sources/stage/cmake
mkdir -p /sources/evidence/h07-cmake
sed -i '/"lib64"/s/64//' Modules/GNUInstallDirs.cmake
./bootstrap --prefix=/usr --parallel=8 --system-libs --mandir=/share/man \
 --no-system-jsoncpp --no-system-cppdap --no-system-librhash \
 --docdir=/share/doc/cmake-4.4.2
make
chown -R tester:tester .
su tester -c 'bin/ctest -j8 --output-on-failure --output-junit full-suite.xml' \
 2>&1 | tee /sources/evidence/h07-cmake/check.log
cp full-suite.xml /sources/evidence/h07-cmake/
make DESTDIR=/sources/stage/cmake install
mkdir -p /sources/stage/cmake/usr/share/doc/cmake
cp -a Licenses /sources/stage/cmake/usr/share/doc/cmake/
# Preserve all bundled third-party notices alongside the aggregate inventory.
find Utilities -type f \( -iname '*license*' -o -iname '*copying*' -o -iname '*copyright*' \) -print0 | \
 tar --null -T - -czf /sources/stage/cmake/usr/share/doc/cmake/bundled-notices.tar.gz
mkdir -p /sources/stage/cmake/usr/share/doc/cmake
cat LICENSE.rst > /sources/stage/cmake/usr/share/doc/cmake/copyright
