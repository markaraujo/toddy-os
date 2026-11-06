#!/bin/bash
# Frozen LFS 13.1-systemd, 5.3; GCC pass 1 is deliberately degraded.
source /opt/toddy-build/scripts/build/h04/common.sh
unpack gcc-16.2.0.tar.xz
cd gcc-16.2.0
unpack mpfr-4.2.2.tar.xz
mv mpfr-4.2.2 mpfr
unpack gmp-6.3.0.tar.xz
mv gmp-6.3.0 gmp
unpack mpc-1.4.1.tar.xz
mv mpc-1.4.1 mpc
sed -e '/m64=/s/lib64/lib/' -i.orig gcc/config/i386/t-linux64
mkdir build
cd build
../configure --target="$LFS_TGT" --prefix="$LFS/tools" \
    --with-glibc-version=2.44 --with-sysroot="$LFS" --with-newlib \
    --without-headers --enable-default-pie --enable-default-ssp \
    --disable-fixincludes --disable-nls --disable-shared --disable-multilib \
    --disable-threads --disable-libatomic --disable-libgomp --disable-libquadmath \
    --disable-libssp --disable-libvtv --disable-libstdcxx --enable-languages=c,c++
make
make install
cat ../gcc/{limitx,glimits,limity}.h > "$("$LFS_TGT-gcc" -print-file-name=include)/limits.h"
cp config.log "$LFS/sources/evidence/h04-gcc-config.log"
cd "$LFS/sources"
rm -rf gcc-16.2.0
