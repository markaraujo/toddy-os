#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
cd "$LFS/sources"
python3 "$SOURCE_TOOL" mpc-1.4.1.tar.xz
chroot_run < /opt/toddy-build/scripts/build/h07/mpc-inner.sh
python3 /opt/toddy-build/scripts/build/stage_package.py mpc 1.4.1-1 \
 "$LFS/sources/stage/mpc" --depends 'glibc (>= 2.44-1), gmp, mpfr' --source mpc-1.4.1.tar.xz \
 --recipe /opt/toddy-build/scripts/build/h07/mpc.sh --install
rm -rf "$LFS/sources/mpc-1.4.1"
