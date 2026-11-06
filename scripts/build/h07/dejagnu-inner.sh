#!/bin/bash
# Frozen LFS 13.1-systemd chapter 8: dejagnu; staged install.
set -euo pipefail
cd /sources/dejagnu-1.6.3
test ! -e /sources/stage/dejagnu
mkdir -v build
cd       build

../configure --prefix=/usr
makeinfo --html --no-split -o doc/dejagnu.html ../doc/dejagnu.texi
makeinfo --plaintext       -o doc/dejagnu.txt  ../doc/dejagnu.texi

make check

make DESTDIR=/sources/stage/dejagnu install
install -v -dm755  /sources/stage/dejagnu/usr/share/doc/dejagnu-1.6.3
install -v -m644   doc/dejagnu.{html,txt} /sources/stage/dejagnu/usr/share/doc/dejagnu-1.6.3
mkdir -p /sources/stage/dejagnu/usr/share/doc/dejagnu
cp ../COPYING /sources/stage/dejagnu/usr/share/doc/dejagnu/copyright
