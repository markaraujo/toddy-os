#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
cd "$LFS/sources"
python3 "$SOURCE_TOOL" libmd-1.3.0.tar.xz
chroot_run < /opt/toddy-build/scripts/build/h07/libmd-inner.sh
python3 /opt/toddy-build/scripts/build/stage_package.py libmd 1.3.0-1 \
 "$LFS/sources/stage/libmd" --depends 'glibc (>= 2.44-1)' --source libmd-1.3.0.tar.xz \
 --recipe /opt/toddy-build/scripts/build/h07/libmd.sh --install
