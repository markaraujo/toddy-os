#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
python3 /opt/toddy-build/scripts/build/h11/require_gate.py
cd "$LFS/sources"
python3 "$SOURCE_TOOL" libburn-1.5.8.tar.gz
chroot_run <<'INNER'
set -euo pipefail
cd /sources/libburn-1.5.8
test ! -e /sources/stage/libburn
mkdir -p /sources/evidence/h11-libburn
./configure --prefix=/usr --disable-static --disable-ldconfig-at-install --disable-libcdio
cp config.log /sources/evidence/h11-libburn/configure.log
make
# Frozen BLFS explicitly reports no upstream test suite for this package.
make DESTDIR=/sources/stage/libburn install
rm /sources/stage/libburn/usr/lib/libburn.la
install -Dm644 COPYING /sources/stage/libburn/usr/share/doc/libburn/copyright
cp COPYRIGHT AUTHORS README /sources/stage/libburn/usr/share/doc/libburn/
INNER
python3 /opt/toddy-build/scripts/build/stage_package.py libburn 1.5.8-1 \
 "$LFS/sources/stage/libburn" --depends 'glibc' \
 --source libburn-1.5.8.tar.gz --recipe /opt/toddy-build/scripts/build/h11/libburn.sh --install
