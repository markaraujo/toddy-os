#!/bin/bash
# LFS 13.1-systemd chapter 6: patch
# Derived by scripts/derive_temporary_recipes.py; review before execution.
source /opt/toddy-build/scripts/build/h04/common.sh
unpack patch-2.8.tar.xz
cd patch-2.8
./configure --prefix=/usr   \
            --host=$LFS_TGT \
            --build=$(build-aux/config.guess)

make

make DESTDIR=$LFS install

if [[ -f config.log ]]; then cp config.log "$LFS/sources/evidence/h05-patch-config.log"; fi
cd "$LFS/sources"
rm -rf patch-2.8
