#!/bin/bash
# Supplemental source additions frozen in ADR-0024.
set -euo pipefail
cd /sources/googletest-1.18.0
test ! -e /sources/stage/googletest
mkdir -p /sources/evidence/h07-googletest
cmake -S . -B build -G Ninja -DCMAKE_INSTALL_PREFIX=/usr \
 -DCMAKE_INSTALL_LIBDIR=lib -DCMAKE_BUILD_TYPE=Release -DBUILD_SHARED_LIBS=ON \
 -Dgtest_build_tests=ON -Dgmock_build_tests=ON
cmake --build build --parallel 8
chown -R tester:tester .
su tester -c 'ctest --test-dir build -j8 --output-on-failure --output-junit full-suite.xml' \
 2>&1 | tee /sources/evidence/h07-googletest/check.log
cp build/full-suite.xml /sources/evidence/h07-googletest/
DESTDIR=/sources/stage/googletest cmake --install build
mkdir -p /sources/stage/googletest/usr/share/doc/googletest
cat LICENSE > /sources/stage/googletest/usr/share/doc/googletest/copyright
