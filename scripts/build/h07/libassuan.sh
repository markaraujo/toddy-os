#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
cd "$LFS/sources"
python3 "$SOURCE_TOOL" libassuan-3.0.2.tar.bz2
chroot_run < /opt/toddy-build/scripts/build/h07/libassuan-inner.sh
python3 /opt/toddy-build/scripts/build/stage_package.py libassuan 3.0.2-1 \
 "$LFS/sources/stage/libassuan" --depends 'glibc (>= 2.44-1), libgpg-error' --source libassuan-3.0.2.tar.bz2 \
 --recipe /opt/toddy-build/scripts/build/h07/libassuan.sh --install
