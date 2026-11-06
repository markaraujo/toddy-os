#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
cd "$LFS/sources"
python3 "$SOURCE_TOOL" libgpg-error-1.61.tar.bz2
chroot_run < /opt/toddy-build/scripts/build/h07/libgpg-error-inner.sh
python3 /opt/toddy-build/scripts/build/stage_package.py libgpg-error 1.61-1 \
 "$LFS/sources/stage/libgpg-error" --depends 'glibc (>= 2.44-1)' --source libgpg-error-1.61.tar.bz2 \
 --recipe /opt/toddy-build/scripts/build/h07/libgpg-error.sh --install
