#!/bin/bash
# Frozen LFS 13.1-systemd 8.7; Makefile PREFIX staging adaptation.
set -euo pipefail
cd /sources/bzip2-1.0.8
patch -Np1 -i ../bzip2-1.0.8-install_docs-1.patch
sed -i 's@\(ln -s -f \)$(PREFIX)/bin/@\1@' Makefile
sed -i 's@(PREFIX)/man@(PREFIX)/share/man@g' Makefile
make -f Makefile-libbz2_so
make clean
make
stage=/sources/stage/bzip2
test ! -e "$stage"
make PREFIX="$stage/usr" install
mkdir -p "$stage/usr/lib"
cp -av libbz2.so.* "$stage/usr/lib"
ln -sfv libbz2.so.1.0.8 "$stage/usr/lib/libbz2.so"
ln -sfv libbz2.so.1.0.8 "$stage/usr/lib/libbz2.so.1"
cp -v bzip2-shared "$stage/usr/bin/bzip2"
for binary in bzcat bunzip2; do ln -sfv bzip2 "$stage/usr/bin/$binary"; done
rm -fv "$stage/usr/lib/libbz2.a"
mkdir -p "$stage/usr/share/doc/bzip2"
cp LICENSE "$stage/usr/share/doc/bzip2/copyright"
