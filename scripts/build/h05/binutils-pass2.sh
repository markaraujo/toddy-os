#!/bin/bash
# LFS 13.1-systemd chapter 6: binutils-pass2
# Derived by scripts/derive_temporary_recipes.py; review before execution.
source /opt/toddy-build/scripts/build/h04/common.sh
unpack binutils-2.47.tar.xz
cd binutils-2.47
sed '6031s/$add_dir//' -i ltmain.sh

mkdir -v build
cd       build

../configure                   \
    --prefix=/usr              \
    --build=$(../config.guess) \
    --host=$LFS_TGT            \
    --disable-nls              \
    --enable-shared            \
    --enable-gprofng=no        \
    --disable-werror           \
    --enable-64-bit-bfd        \
    --enable-new-dtags         \
    --enable-default-hash-style=gnu

make

make DESTDIR=$LFS install

rm -v $LFS/usr/lib/lib{bfd,ctf,ctf-nobfd,opcodes,sframe}.{a,la}

if [[ -f config.log ]]; then cp config.log "$LFS/sources/evidence/h05-binutils-pass2-config.log"; fi
cd "$LFS/sources"
rm -rf binutils-2.47
