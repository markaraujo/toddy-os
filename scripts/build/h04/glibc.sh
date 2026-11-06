#!/bin/bash
# Frozen LFS 13.1-systemd, 5.5. Critical final libc tests belong to H07.
source /opt/toddy-build/scripts/build/h04/common.sh
unpack glibc-2.44.tar.xz
verify glibc-fhs-1.patch
verify glibc-2.44-upstream_fixes-1.patch
ln -sfv ../lib/ld-linux-x86-64.so.2 "$LFS/lib64"
ln -sfv ../lib/ld-linux-x86-64.so.2 "$LFS/lib64/ld-lsb-x86-64.so.3"
cd glibc-2.44
patch -Np1 -i ../glibc-fhs-1.patch
patch -Np1 -i ../glibc-2.44-upstream_fixes-1.patch
mkdir build
cd build
echo 'rootsbindir=/usr/sbin' > configparms
../configure --prefix=/usr --host="$LFS_TGT" --build="$(../scripts/config.guess)" \
    --disable-nscd libc_cv_slibdir=/usr/lib --enable-kernel=5.10
make
make DESTDIR="$LFS" install
sed '/RTLDLIST=/s@/usr@@g' -i "$LFS/usr/bin/ldd"
cp config.log "$LFS/sources/evidence/h04-glibc-config.log"
cd "$LFS/sources"
rm -rf glibc-2.44
