#!/bin/bash
# LFS 13.1-systemd chapter 6: bash
# Derived by scripts/derive_temporary_recipes.py; review before execution.
source /opt/toddy-build/scripts/build/h04/common.sh
unpack bash-5.3.tar.gz
cd bash-5.3
./configure --prefix=/usr                      \
            --build=$(sh support/config.guess) \
            --host=$LFS_TGT                    \
            --without-bash-malloc              \
            --docdir=/usr/share/doc/bash-5.3

make

make DESTDIR=$LFS install

ln -sv bash $LFS/bin/sh

if [[ -f config.log ]]; then cp config.log "$LFS/sources/evidence/h05-bash-config.log"; fi
cd "$LFS/sources"
rm -rf bash-5.3
