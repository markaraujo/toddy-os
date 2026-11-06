#!/bin/bash
# Frozen LFS 13.1-systemd chapter 8: flex, staged native installation.
set -euo pipefail
cd /sources/flex-2.6.4
test ! -e /sources/stage/flex
./configure --prefix=/usr    \
            --disable-static \
            --docdir=/usr/share/doc/flex-2.6.4

make

make check

make DESTDIR=/sources/stage/flex install

ln -sv flex   /sources/stage/flex/usr/bin/lex
ln -sv flex.1 /sources/stage/flex/usr/share/man/man1/lex.1
mkdir -p /sources/stage/flex/usr/share/doc/flex
cp COPYING /sources/stage/flex/usr/share/doc/flex/copyright
