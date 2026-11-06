#!/bin/bash
# Frozen LFS 13.1-systemd sections 8.60-8.66; build only in guarded target.
set -euo pipefail
cd /sources/kmod-34.2
test ! -e /sources/stage/kmod
mkdir -p /sources/evidence/h07-kmod
mkdir build
cd build
meson setup --prefix=/usr .. --buildtype=release -D manpages=false
ninja
# LFS 13.1 8.60: suite needs raw kernel headers; module tests remain H09.
DESTDIR=/sources/stage/kmod ninja install
find . -type f \( -name '*.log' -o -name '*.trs' -o -name '*.sum' \) -print0 | \
 tar --null -T - -czf /sources/evidence/h07-kmod/test-reports.tar.gz
mkdir -p /sources/stage/kmod/usr/share/doc/kmod
cat ../COPYING > /sources/stage/kmod/usr/share/doc/kmod/copyright
