#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
cd "$LFS/sources"
python3 "$SOURCE_TOOL" libcap-2.78.tar.xz
chroot_run < /opt/toddy-build/scripts/build/h07/libcap-inner.sh
python3 /opt/toddy-build/scripts/build/stage_package.py libcap 2.78-1 \
 "$LFS/sources/stage/libcap" --depends 'glibc (>= 2.44-1)' --source libcap-2.78.tar.xz \
 --recipe /opt/toddy-build/scripts/build/h07/libcap.sh --install
rm -rf "$LFS/sources/libcap-2.78"
