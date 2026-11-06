#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
cd "$LFS/sources"
python3 "$SOURCE_TOOL" libtool-2.6.2.tar.xz
chroot_run < /opt/toddy-build/scripts/build/h07/libtool-inner.sh
python3 /opt/toddy-build/scripts/build/stage_package.py libtool 2.6.2-1 \
 "$LFS/sources/stage/libtool" --depends 'glibc (>= 2.44-1)' --source libtool-2.6.2.tar.xz \
 --recipe /opt/toddy-build/scripts/build/h07/libtool.sh --install
