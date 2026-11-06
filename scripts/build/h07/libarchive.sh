#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
cd "$LFS/sources"
python3 "$SOURCE_TOOL" libarchive-3.8.11.tar.xz
chroot_run < /opt/toddy-build/scripts/build/h07/libarchive-inner.sh
python3 /opt/toddy-build/scripts/build/stage_package.py libarchive 3.8.11-1 \
 "$LFS/sources/stage/libarchive" --depends 'glibc (>= 2.44-1), openssl, zlib, bzip2, xz, zstd, acl, libxcrypt' --source libarchive-3.8.11.tar.xz \
 --recipe /opt/toddy-build/scripts/build/h07/libarchive.sh --install
