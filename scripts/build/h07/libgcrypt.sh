#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
cd "$LFS/sources"
python3 "$SOURCE_TOOL" libgcrypt-1.12.4.tar.bz2
chroot_run < /opt/toddy-build/scripts/build/h07/libgcrypt-inner.sh
python3 /opt/toddy-build/scripts/build/stage_package.py libgcrypt 1.12.4-1 \
 "$LFS/sources/stage/libgcrypt" --depends 'glibc (>= 2.44-1), libgpg-error' --source libgcrypt-1.12.4.tar.bz2 \
 --recipe /opt/toddy-build/scripts/build/h07/libgcrypt.sh --install
