#!/bin/bash
# Frozen LFS 13.1-systemd, 5.2. Pass 1 is not the final tested binutils.
source /opt/toddy-build/scripts/build/h04/common.sh
unpack binutils-2.47.tar.xz
cd binutils-2.47
mkdir build
cd build
../configure --prefix="$LFS/tools" --with-sysroot="$LFS" --target="$LFS_TGT" \
    --disable-nls --enable-gprofng=no --disable-werror --enable-new-dtags \
    --enable-default-hash-style=gnu
make
make install
cp config.log "$LFS/sources/evidence/h04-binutils-config.log"
cd "$LFS/sources"
rm -rf binutils-2.47
