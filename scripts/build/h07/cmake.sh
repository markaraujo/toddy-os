#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
cd "$LFS/sources"
python3 "$SOURCE_TOOL" cmake-4.4.2.tar.gz
chroot_run < /opt/toddy-build/scripts/build/h07/cmake-inner.sh
python3 /opt/toddy-build/scripts/build/stage_package.py cmake 4.4.2-1 \
 "$LFS/sources/stage/cmake" --depends 'glibc (>= 2.44-1), gcc-runtime, curl, libuv, libarchive, expat, zlib, bzip2, xz, zstd, ncurses' --source cmake-4.4.2.tar.gz \
 --recipe /opt/toddy-build/scripts/build/h07/cmake.sh --install
