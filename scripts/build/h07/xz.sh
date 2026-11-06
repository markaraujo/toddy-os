#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
cd "$LFS/sources"
python3 "$SOURCE_TOOL" xz-5.8.4.tar.xz
chroot_run < /opt/toddy-build/scripts/build/h07/xz-inner.sh
python3 /opt/toddy-build/scripts/build/stage_package.py xz 5.8.4-1 \
    "$LFS/sources/stage/xz" --depends 'glibc (>= 2.44-1)' --source xz-5.8.4.tar.xz \
    --recipe /opt/toddy-build/scripts/build/h07/xz.sh --install
rm -rf "$LFS/sources/xz-5.8.4"
