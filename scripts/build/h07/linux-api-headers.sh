#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
cd "$LFS/sources"
python3 "$SOURCE_TOOL" linux-7.1.8.tar.xz
chroot_run <<'INNER'
set -euo pipefail
cd /sources/linux-7.1.8
test ! -e /sources/stage/linux-api-headers
make mrproper
make headers
find usr/include -type f ! -name '*.h' -delete
mkdir -p /sources/stage/linux-api-headers/usr
cp -a usr/include /sources/stage/linux-api-headers/usr/
mkdir -p /sources/stage/linux-api-headers/usr/share/doc/linux-api-headers
cp COPYING /sources/stage/linux-api-headers/usr/share/doc/linux-api-headers/copyright
cp -a LICENSES /sources/stage/linux-api-headers/usr/share/doc/linux-api-headers/
INNER
python3 /opt/toddy-build/scripts/build/stage_package.py linux-api-headers 7.1.8-1 \
 "$LFS/sources/stage/linux-api-headers" --source linux-7.1.8.tar.xz \
 --recipe /opt/toddy-build/scripts/build/h07/linux-api-headers.sh --install
