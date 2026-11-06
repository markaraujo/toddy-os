#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
cd "$LFS/sources"
python3 "$SOURCE_TOOL" kmod-34.2.tar.xz
chroot_run < /opt/toddy-build/scripts/build/h07/kmod-inner.sh
python3 /opt/toddy-build/scripts/build/stage_package.py kmod 34.2-1 \
 "$LFS/sources/stage/kmod" --depends 'glibc (>= 2.44-1), xz, zstd, zlib' --source kmod-34.2.tar.xz \
 --recipe /opt/toddy-build/scripts/build/h07/kmod.sh --install
