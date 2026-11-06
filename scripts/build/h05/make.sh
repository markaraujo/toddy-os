#!/bin/bash
# LFS 13.1-systemd chapter 6: make
# Derived by scripts/derive_temporary_recipes.py; review before execution.
source /opt/toddy-build/scripts/build/h04/common.sh
unpack make-4.4.1.tar.gz
cd make-4.4.1
./configure --prefix=/usr   \
            --host=$LFS_TGT \
            --build=$(build-aux/config.guess)

make

make DESTDIR=$LFS install

if [[ -f config.log ]]; then cp config.log "$LFS/sources/evidence/h05-make-config.log"; fi
cd "$LFS/sources"
rm -rf make-4.4.1
