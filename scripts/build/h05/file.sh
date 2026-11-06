#!/bin/bash
# LFS 13.1-systemd chapter 6: file
# Derived by scripts/derive_temporary_recipes.py; review before execution.
source /opt/toddy-build/scripts/build/h04/common.sh
unpack file-5.48.tar.gz
cd file-5.48
mkdir build
pushd build
  ../configure --disable-bzlib      \
               --disable-libseccomp \
               --disable-xzlib      \
               --disable-zlib
  make
popd

./configure --prefix=/usr --host=$LFS_TGT --build=$(./config.guess)

make FILE_COMPILE=$(pwd)/build/src/file

make DESTDIR=$LFS install

rm -v $LFS/usr/lib/libmagic.la

if [[ -f config.log ]]; then cp config.log "$LFS/sources/evidence/h05-file-config.log"; fi
cd "$LFS/sources"
rm -rf file-5.48
