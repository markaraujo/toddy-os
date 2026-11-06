#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
cd "$LFS/sources"
python3 "$SOURCE_TOOL" gcc-16.2.0.tar.xz
chroot_run < /opt/toddy-build/scripts/build/h07/gcc-build-inner.sh
