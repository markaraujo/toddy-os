#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
cd "$LFS/sources"
python3 "$SOURCE_TOOL" util-linux-2.42.4.tar.xz
chroot_run < /opt/toddy-build/scripts/build/h07/util-linux-inner.sh
python3 /opt/toddy-build/scripts/build/stage_package.py util-linux 2.42.4-1 \
 "$LFS/sources/stage/util-linux" --depends 'glibc (>= 2.44-1), ncurses, zlib, readline, zstd' --source util-linux-2.42.4.tar.xz  \
 --recipe /opt/toddy-build/scripts/build/h07/util-linux.sh --install
