#!/bin/bash
# LFS 13.1-systemd chapter 6: diffutils
# Derived by scripts/derive_temporary_recipes.py; review before execution.
source /opt/toddy-build/scripts/build/h04/common.sh
unpack diffutils-3.12.tar.xz
cd diffutils-3.12
./configure --prefix=/usr   \
            --host=$LFS_TGT \
            gl_cv_func_strcasecmp_works=yes \
            --build=$(./build-aux/config.guess)

make

make DESTDIR=$LFS install

if [[ -f config.log ]]; then cp config.log "$LFS/sources/evidence/h05-diffutils-config.log"; fi
cd "$LFS/sources"
rm -rf diffutils-3.12
