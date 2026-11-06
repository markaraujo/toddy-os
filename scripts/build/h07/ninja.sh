#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
cd "$LFS/sources"
python3 "$SOURCE_TOOL" ninja-1.13.2.tar.gz
chroot_run < /opt/toddy-build/scripts/build/h07/ninja-inner.sh
python3 /opt/toddy-build/scripts/build/stage_package.py ninja 1.13.2-1 \
    "$LFS/sources/stage/ninja" --depends 'glibc (>= 2.44-1)' --source ninja-1.13.2.tar.gz \
    --recipe /opt/toddy-build/scripts/build/h07/ninja.sh --install
rm -rf "$LFS/sources/ninja-1.13.2"
