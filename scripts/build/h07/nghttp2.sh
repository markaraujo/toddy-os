#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
cd "$LFS/sources"
python3 "$SOURCE_TOOL" nghttp2-1.71.0.tar.xz
chroot_run < /opt/toddy-build/scripts/build/h07/nghttp2-inner.sh
python3 /opt/toddy-build/scripts/build/stage_package.py nghttp2 1.71.0-1 \
 "$LFS/sources/stage/nghttp2" --depends 'glibc (>= 2.44-1), gcc-runtime' --source nghttp2-1.71.0.tar.xz \
 --recipe /opt/toddy-build/scripts/build/h07/nghttp2.sh --install
