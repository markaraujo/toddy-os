#!/bin/bash
# LFS 13.1-systemd chapter 6: sed
# Derived by scripts/derive_temporary_recipes.py; review before execution.
source /opt/toddy-build/scripts/build/h04/common.sh
unpack sed-4.10.tar.xz
cd sed-4.10
./configure --prefix=/usr   \
            --host=$LFS_TGT \
            --build=$(./build-aux/config.guess)

make

make DESTDIR=$LFS install

if [[ -f config.log ]]; then cp config.log "$LFS/sources/evidence/h05-sed-config.log"; fi
cd "$LFS/sources"
rm -rf sed-4.10
