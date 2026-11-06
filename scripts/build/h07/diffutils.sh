#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
cd "$LFS/sources"
python3 "$SOURCE_TOOL" diffutils-3.12.tar.xz
chroot_run < /opt/toddy-build/scripts/build/h07/diffutils-inner.sh
python3 /opt/toddy-build/scripts/build/stage_package.py diffutils 3.12-1 \
 "$LFS/sources/stage/diffutils" --depends 'glibc (>= 2.44-1)' --source diffutils-3.12.tar.xz \
 --recipe /opt/toddy-build/scripts/build/h07/diffutils.sh --install
