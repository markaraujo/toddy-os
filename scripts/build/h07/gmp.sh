#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
cd "$LFS/sources"
python3 "$SOURCE_TOOL" gmp-6.3.0.tar.xz
chroot_run < /opt/toddy-build/scripts/build/h07/gmp-inner.sh
python3 /opt/toddy-build/scripts/build/stage_package.py gmp 6.3.0-1 \
 "$LFS/sources/stage/gmp" --depends 'glibc (>= 2.44-1)' --source gmp-6.3.0.tar.xz \
 --recipe /opt/toddy-build/scripts/build/h07/gmp.sh --install
rm -rf "$LFS/sources/gmp-6.3.0"
