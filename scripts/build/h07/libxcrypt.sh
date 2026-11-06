#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
cd "$LFS/sources"
python3 "$SOURCE_TOOL" libxcrypt-4.5.2.tar.xz
chroot_run < /opt/toddy-build/scripts/build/h07/libxcrypt-inner.sh
python3 /opt/toddy-build/scripts/build/stage_package.py libxcrypt 4.5.2-1 \
 "$LFS/sources/stage/libxcrypt" --depends 'glibc (>= 2.44-1)' --source libxcrypt-4.5.2.tar.xz \
 --recipe /opt/toddy-build/scripts/build/h07/libxcrypt.sh --install
rm -rf "$LFS/sources/libxcrypt-4.5.2"
