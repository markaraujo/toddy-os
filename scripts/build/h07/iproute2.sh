#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
cd "$LFS/sources"
python3 "$SOURCE_TOOL" iproute2-7.1.0.tar.xz
chroot_run < /opt/toddy-build/scripts/build/h07/iproute2-inner.sh
python3 /opt/toddy-build/scripts/build/stage_package.py iproute2 7.1.0-1 \
 "$LFS/sources/stage/iproute2" --depends 'glibc (>= 2.44-1), libelf, libcap' --source iproute2-7.1.0.tar.xz \
 --recipe /opt/toddy-build/scripts/build/h07/iproute2.sh --install
