#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
cd "$LFS/sources"
python3 "$SOURCE_TOOL" m4-1.4.21.tar.xz
chroot_run < /opt/toddy-build/scripts/build/h07/m4-inner.sh
python3 /opt/toddy-build/scripts/build/stage_package.py m4 1.4.21-1 \
    "$LFS/sources/stage/m4" --depends 'glibc (>= 2.44-1)' --source m4-1.4.21.tar.xz \
    --recipe /opt/toddy-build/scripts/build/h07/m4.sh --install
rm -rf "$LFS/sources/m4-1.4.21"
