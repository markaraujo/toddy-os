#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
cd "$LFS/sources"
python3 "$SOURCE_TOOL" libksba-1.8.1.tar.bz2
chroot_run < /opt/toddy-build/scripts/build/h07/libksba-inner.sh
python3 /opt/toddy-build/scripts/build/stage_package.py libksba 1.8.1-1 \
 "$LFS/sources/stage/libksba" --depends 'glibc (>= 2.44-1), libgpg-error' --source libksba-1.8.1.tar.bz2 \
 --recipe /opt/toddy-build/scripts/build/h07/libksba.sh --install
