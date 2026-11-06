#!/bin/bash
# LFS 13.1-systemd chapter 6: gzip
# Derived by scripts/derive_temporary_recipes.py; review before execution.
source /opt/toddy-build/scripts/build/h04/common.sh
unpack gzip-1.14.tar.xz
cd gzip-1.14
./configure --prefix=/usr --host=$LFS_TGT

make

make DESTDIR=$LFS install

if [[ -f config.log ]]; then cp config.log "$LFS/sources/evidence/h05-gzip-config.log"; fi
cd "$LFS/sources"
rm -rf gzip-1.14
