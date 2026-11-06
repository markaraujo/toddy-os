#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
cd "$LFS/sources"
python3 "$SOURCE_TOOL" gawk-5.4.1.tar.xz
chroot_run < /opt/toddy-build/scripts/build/h07/gawk-inner.sh
python3 /opt/toddy-build/scripts/build/stage_package.py gawk 5.4.1-1 \
 "$LFS/sources/stage/gawk" --depends 'glibc (>= 2.44-1), mpfr, gmp' \
 --source gawk-5.4.1.tar.xz --recipe /opt/toddy-build/scripts/build/h07/gawk.sh --install
rm -rf "$LFS/sources/gawk-5.4.1"
