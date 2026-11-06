#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
cd "$LFS/sources"
python3 "$SOURCE_TOOL" libuv-v1.52.1.tar.gz
chroot_run < /opt/toddy-build/scripts/build/h07/libuv-inner.sh
python3 /opt/toddy-build/scripts/build/stage_package.py libuv 1.52.1-1 \
 "$LFS/sources/stage/libuv" --depends 'glibc (>= 2.44-1)' --source libuv-v1.52.1.tar.gz \
 --recipe /opt/toddy-build/scripts/build/h07/libuv.sh --install
