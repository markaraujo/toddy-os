#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
cd "$LFS/sources"
python3 "$SOURCE_TOOL" patch-2.8.1.tar.xz
chroot_run < /opt/toddy-build/scripts/build/h07/patch-inner.sh
python3 /opt/toddy-build/scripts/build/stage_package.py patch 2.8.1-1 \
 "$LFS/sources/stage/patch" --depends 'glibc (>= 2.44-1), attr' --source patch-2.8.1.tar.xz \
 --recipe /opt/toddy-build/scripts/build/h07/patch.sh --install
