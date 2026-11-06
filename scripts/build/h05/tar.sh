#!/bin/bash
# LFS 13.1-systemd chapter 6: tar
# Derived by scripts/derive_temporary_recipes.py; review before execution.
source /opt/toddy-build/scripts/build/h04/common.sh
unpack tar-1.35.tar.xz
cd tar-1.35
./configure --prefix=/usr   \
            --host=$LFS_TGT \
            --build=$(build-aux/config.guess)

make

make DESTDIR=$LFS install

if [[ -f config.log ]]; then cp config.log "$LFS/sources/evidence/h05-tar-config.log"; fi
cd "$LFS/sources"
rm -rf tar-1.35
