#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
cd "$LFS/sources"
python3 "$SOURCE_TOOL" bc-7.0.3.tar.xz
chroot_run < /opt/toddy-build/scripts/build/h07/bc-inner.sh
python3 /opt/toddy-build/scripts/build/stage_package.py bc 7.0.3-1 \
    "$LFS/sources/stage/bc" --depends 'glibc (>= 2.44-1)' --source bc-7.0.3.tar.xz \
    --recipe /opt/toddy-build/scripts/build/h07/bc.sh --install
rm -rf "$LFS/sources/bc-7.0.3"
