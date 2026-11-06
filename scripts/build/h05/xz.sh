#!/bin/bash
# LFS 13.1-systemd chapter 6: xz
# Derived by scripts/derive_temporary_recipes.py; review before execution.
source /opt/toddy-build/scripts/build/h04/common.sh
unpack xz-5.8.3.tar.xz
cd xz-5.8.3
./configure --prefix=/usr                     \
            --host=$LFS_TGT                   \
            --build=$(build-aux/config.guess) \
            --disable-static                  \
            --docdir=/usr/share/doc/xz-5.8.3

make

make DESTDIR=$LFS install

rm -v $LFS/usr/lib/liblzma.la

if [[ -f config.log ]]; then cp config.log "$LFS/sources/evidence/h05-xz-config.log"; fi
cd "$LFS/sources"
rm -rf xz-5.8.3
