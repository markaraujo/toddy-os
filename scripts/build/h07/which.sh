#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
cd "$LFS/sources"
python3 "$SOURCE_TOOL" which-2.25.tar.gz
chroot_run <<'INNER'
set -euo pipefail
cd /sources/which-2.25
./configure --prefix=/usr
make
make check
make DESTDIR=/sources/stage/which install
install -Dm644 COPYING /sources/stage/which/usr/share/doc/which/copyright
INNER
python3 /opt/toddy-build/scripts/build/stage_package.py which 2.25-1 \
 "$LFS/sources/stage/which" --depends glibc --source which-2.25.tar.gz \
 --recipe /opt/toddy-build/scripts/build/h07/which.sh --install
