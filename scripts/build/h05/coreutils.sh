#!/bin/bash
# LFS 13.1-systemd chapter 6: coreutils
# Derived by scripts/derive_temporary_recipes.py; review before execution.
source /opt/toddy-build/scripts/build/h04/common.sh
unpack coreutils-9.11.tar.xz
cd coreutils-9.11
./configure --prefix=/usr                     \
            --host=$LFS_TGT                   \
            --build=$(build-aux/config.guess) \
            --enable-install-program=hostname

make

make DESTDIR=$LFS install

mv -v $LFS/usr/bin/chroot              $LFS/usr/sbin
mkdir -pv $LFS/usr/share/man/man8
mv -v $LFS/usr/share/man/man1/chroot.1 $LFS/usr/share/man/man8/chroot.8
sed -i 's/"1"/"8"/'                    $LFS/usr/share/man/man8/chroot.8

if [[ -f config.log ]]; then cp config.log "$LFS/sources/evidence/h05-coreutils-config.log"; fi
cd "$LFS/sources"
rm -rf coreutils-9.11
