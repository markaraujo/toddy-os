#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
cd "$LFS/sources"
python3 "$SOURCE_TOOL" mpfr-4.2.2.tar.xz
chroot_run < /opt/toddy-build/scripts/build/h07/mpfr-inner.sh
python3 /opt/toddy-build/scripts/build/stage_package.py mpfr 4.2.2-1 \
 "$LFS/sources/stage/mpfr" --depends 'glibc (>= 2.44-1), gmp' --source mpfr-4.2.2.tar.xz \
 --recipe /opt/toddy-build/scripts/build/h07/mpfr.sh --install
rm -rf "$LFS/sources/mpfr-4.2.2"
