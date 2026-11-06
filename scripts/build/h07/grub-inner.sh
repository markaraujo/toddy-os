#!/bin/bash
# Frozen LFS 13.1-systemd sections 8.60-8.66; build only in guarded target.
set -euo pipefail
cd /sources/grub-2.14
test ! -e /sources/stage/grub
mkdir -p /sources/evidence/h07-grub
unset {C,CPP,CXX,LD}FLAGS
sed 's/--image-base/--nonexist-linker-option/' -i configure
./configure --prefix=/usr --sysconfdir=/etc --disable-efiemu --disable-werror
make
make DESTDIR=/sources/stage/grub install
make clean
./configure --prefix=/usr --sysconfdir=/etc --target=x86_64 --with-platform=efi --disable-efiemu --disable-werror
make
make DESTDIR=/sources/stage/grub install
# LFS 8.65 discourages this limited-environment suite; real BIOS/UEFI boot
# acceptance remains mandatory. No grub-install or disk operation occurs here.
find . -type f \( -name '*.log' -o -name '*.trs' -o -name '*.sum' \) -print0 | \
 tar --null -T - -czf /sources/evidence/h07-grub/test-reports.tar.gz
mkdir -p /sources/stage/grub/usr/share/doc/grub
cat COPYING > /sources/stage/grub/usr/share/doc/grub/copyright
