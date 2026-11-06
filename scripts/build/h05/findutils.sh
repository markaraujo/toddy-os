#!/bin/bash
# LFS 13.1-systemd chapter 6: findutils
# Derived by scripts/derive_temporary_recipes.py; review before execution.
source /opt/toddy-build/scripts/build/h04/common.sh
unpack findutils-4.11.0.tar.xz
cd findutils-4.11.0
./configure --prefix=/usr                   \
            --localstatedir=/var/lib/locate \
            --host=$LFS_TGT                 \
            --build=$(build-aux/config.guess)

make

make DESTDIR=$LFS install

if [[ -f config.log ]]; then cp config.log "$LFS/sources/evidence/h05-findutils-config.log"; fi
cd "$LFS/sources"
rm -rf findutils-4.11.0
