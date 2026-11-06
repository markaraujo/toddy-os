#!/bin/bash
# LFS 13.1-systemd chapter 6: gawk
# Derived by scripts/derive_temporary_recipes.py; review before execution.
source /opt/toddy-build/scripts/build/h04/common.sh
unpack gawk-5.4.1.tar.xz
cd gawk-5.4.1
sed -i 's/extras//' Makefile.in

./configure --prefix=/usr   \
            --host=$LFS_TGT \
            --build=$(build-aux/config.guess)

make

make DESTDIR=$LFS install

if [[ -f config.log ]]; then cp config.log "$LFS/sources/evidence/h05-gawk-config.log"; fi
cd "$LFS/sources"
rm -rf gawk-5.4.1
