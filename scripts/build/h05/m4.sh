#!/bin/bash
# LFS 13.1-systemd chapter 6: m4
# Derived by scripts/derive_temporary_recipes.py; review before execution.
source /opt/toddy-build/scripts/build/h04/common.sh
unpack m4-1.4.21.tar.xz
cd m4-1.4.21
mkdir -p "$LFS/usr/share"
cat > $LFS/usr/share/config.site << EOF
ac_cv_func_posix_spawn_file_actions_addchdir=yes
ac_cv_func_posix_spawn_file_actions_addfchdir=yes
EOF

./configure --prefix=/usr   \
            --host=$LFS_TGT \
            --build=$(build-aux/config.guess)

make

make DESTDIR=$LFS install

if [[ -f config.log ]]; then cp config.log "$LFS/sources/evidence/h05-m4-config.log"; fi
cd "$LFS/sources"
rm -rf m4-1.4.21
