#!/bin/bash
# Frozen LFS 13.1-systemd 8.33; staged replacement avoids in-place shell crash.
set -euo pipefail
cd /sources/ncurses-6.6
test ! -e /sources/stage/ncurses
./configure --prefix=/usr --mandir=/usr/share/man --with-shared \
 --without-debug --without-normal --with-cxx-shared --enable-pc-files \
 --with-pkg-config-libdir=/usr/lib/pkgconfig
make
make DESTDIR=/sources/stage/ncurses install
sed -e 's/^#if.*XOPEN.*$/#if 1/' -i /sources/stage/ncurses/usr/include/curses.h
for lib in ncurses form panel menu; do
 ln -sfv lib${lib}w.so /sources/stage/ncurses/usr/lib/lib${lib}.so
 ln -sfv ${lib}w.pc /sources/stage/ncurses/usr/lib/pkgconfig/${lib}.pc
done
ln -sfv libncursesw.so /sources/stage/ncurses/usr/lib/libcurses.so
cp -v -R doc -T /sources/stage/ncurses/usr/share/doc/ncurses-6.6
mkdir -p /sources/stage/ncurses/usr/share/doc/ncurses
cp COPYING /sources/stage/ncurses/usr/share/doc/ncurses/copyright
# ABI 5 is an optional book alternative for binary-only apps, not required by
# this source-built package set. Interactive upstream tests run after install.
