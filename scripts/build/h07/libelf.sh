#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
cd "$LFS/sources"
python3 "$SOURCE_TOOL" elfutils-0.195.tar.bz2
chroot_run < /opt/toddy-build/scripts/build/h07/libelf-inner.sh
python3 /opt/toddy-build/scripts/build/stage_package.py libelf 0.195-1 \
 "$LFS/sources/stage/libelf" --depends 'glibc (>= 2.44-1), zlib' --source elfutils-0.195.tar.bz2 \
 --recipe /opt/toddy-build/scripts/build/h07/libelf.sh --install
