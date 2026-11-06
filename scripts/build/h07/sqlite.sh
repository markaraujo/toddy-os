#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
cd "$LFS/sources"
python3 "$SOURCE_TOOL" sqlite-autoconf-3530400.tar.gz
chroot_run < /opt/toddy-build/scripts/build/h07/sqlite-inner.sh
python3 /opt/toddy-build/scripts/build/stage_package.py sqlite 3.53.4-1 \
 "$LFS/sources/stage/sqlite" --depends 'glibc (>= 2.44-1), zlib, readline' --source sqlite-autoconf-3530400.tar.gz \
 --recipe /opt/toddy-build/scripts/build/h07/sqlite.sh --install
