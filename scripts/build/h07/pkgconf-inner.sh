#!/bin/bash
# Frozen LFS 13.1-systemd chapter 8: pkgconf; staged install.
set -euo pipefail
cd /sources/pkgconf-3.0.5
test ! -e /sources/stage/pkgconf
tar -xf ../meson-1.12.0.tar.gz

mkdir build
cd    build

python3 ../meson-1.12.0/meson.py setup --prefix=/usr --buildtype=release ..

ninja

ninja test

DESTDIR=/sources/stage/pkgconf ninja install
mv /sources/stage/pkgconf/usr/share/doc/pkgconf{,-3.0.5}

ln -sv pkgconf   /sources/stage/pkgconf/usr/bin/pkg-config
ln -sv pkgconf.1 /sources/stage/pkgconf/usr/share/man/man1/pkg-config.1
mkdir -p /sources/stage/pkgconf/usr/share/doc/pkgconf
cp ../COPYING /sources/stage/pkgconf/usr/share/doc/pkgconf/copyright
