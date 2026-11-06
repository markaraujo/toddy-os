#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
cd "$LFS/sources"
python3 "$SOURCE_TOOL" inetutils-2.8.tar.gz
chroot_run < /opt/toddy-build/scripts/build/h07/inetutils-inner.sh
python3 /opt/toddy-build/scripts/build/stage_package.py inetutils 2.8-1 \
 "$LFS/sources/stage/inetutils" --depends 'glibc (>= 2.44-1), ncurses, readline' --source inetutils-2.8.tar.gz \
 --recipe /opt/toddy-build/scripts/build/h07/inetutils.sh --install
