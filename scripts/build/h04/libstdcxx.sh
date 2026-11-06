#!/bin/bash
# Frozen LFS 13.1-systemd, 5.6; fresh GCC source tree as directed.
source /opt/toddy-build/scripts/build/h04/common.sh
unpack gcc-16.2.0.tar.xz
cd gcc-16.2.0
mkdir build
cd build
../libstdc++-v3/configure --host="$LFS_TGT" --build="$(../config.guess)" \
    CXX="$LFS_TGT-gcc" --prefix=/usr --disable-multilib --disable-nls \
    --disable-libstdcxx-pch --with-gxx-include-dir="/tools/$LFS_TGT/include/c++/16.2.0"
make
make DESTDIR="$LFS" install
rm -v "$LFS"/usr/lib/lib{stdc++{,exp,fs},supc++}.la
cp config.log "$LFS/sources/evidence/h04-libstdcxx-config.log"
cd "$LFS/sources"
rm -rf gcc-16.2.0
