#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
cd "$LFS/sources"
python3 "$SOURCE_TOOL" findutils-4.11.0.tar.xz
chroot_run < /opt/toddy-build/scripts/build/h07/findutils-inner.sh
python3 /opt/toddy-build/scripts/build/stage_package.py findutils 4.11.0-1 \
 "$LFS/sources/stage/findutils" --depends 'glibc (>= 2.44-1)' --source findutils-4.11.0.tar.xz \
 --recipe /opt/toddy-build/scripts/build/h07/findutils.sh --install
