#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
cd "$LFS/sources"
python3 "$SOURCE_TOOL" expect5.45.4.tar.gz
python3 "$SOURCE_TOOL" --verify-only expect-5.45.4-gcc15-1.patch
chroot_run < /opt/toddy-build/scripts/build/h07/expect-inner.sh
python3 /opt/toddy-build/scripts/build/stage_package.py expect 5.45.4-1 \
    "$LFS/sources/stage/expect" --depends 'glibc (>= 2.44-1), tcl' --source expect5.45.4.tar.gz --source expect-5.45.4-gcc15-1.patch \
    --recipe /opt/toddy-build/scripts/build/h07/expect.sh --install
rm -rf "$LFS/sources/expect5.45.4"
