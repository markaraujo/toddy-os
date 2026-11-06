#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
python3 /opt/toddy-build/scripts/build/h11/require_gate.py
cd "$LFS/sources"
python3 "$SOURCE_TOOL" libisofs-1.5.8.pl02.tar.gz
chroot_run <<'INNER'
set -euo pipefail
cd /sources/libisofs-1.5.8
test ! -e /sources/stage/libisofs
mkdir -p /sources/evidence/h11-libisofs
./configure --prefix=/usr --disable-static --disable-ldconfig-at-install --disable-libjte
for feature in Libisofs_with_aaip_acL Libisofs_with_aaip_xattR Libisofs_with_zliB; do
 grep -F -- "-D$feature" Makefile
done
cp config.log /sources/evidence/h11-libisofs/configure.log
make
# Frozen BLFS explicitly reports no upstream test suite for this package.
make DESTDIR=/sources/stage/libisofs install
rm /sources/stage/libisofs/usr/lib/libisofs.la
install -Dm644 COPYING /sources/stage/libisofs/usr/share/doc/libisofs/copyright
cp COPYRIGHT AUTHORS README /sources/stage/libisofs/usr/share/doc/libisofs/
INNER
python3 /opt/toddy-build/scripts/build/stage_package.py libisofs 1.5.8.pl02-1 \
 "$LFS/sources/stage/libisofs" --depends 'glibc, acl, zlib' \
 --source libisofs-1.5.8.pl02.tar.gz --recipe /opt/toddy-build/scripts/build/h11/libisofs.sh --install
