#!/bin/bash
# LFS 13.1-systemd chapter 6: grep
# Derived by scripts/derive_temporary_recipes.py; review before execution.
source /opt/toddy-build/scripts/build/h04/common.sh
unpack grep-3.12.tar.xz
cd grep-3.12
./configure --prefix=/usr   \
            --host=$LFS_TGT \
            --build=$(./build-aux/config.guess)

make

make DESTDIR=$LFS install

if [[ -f config.log ]]; then cp config.log "$LFS/sources/evidence/h05-grep-config.log"; fi
cd "$LFS/sources"
rm -rf grep-3.12
