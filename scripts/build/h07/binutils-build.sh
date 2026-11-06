#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
cd "$LFS/sources"
python3 "$SOURCE_TOOL" binutils-2.47.tar.xz
chroot_run < /opt/toddy-build/scripts/build/h07/binutils-build-inner.sh
