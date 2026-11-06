#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
cd "$LFS/sources"
python3 "$SOURCE_TOOL" gzip-1.14.tar.xz
chroot_run < /opt/toddy-build/scripts/build/h07/gzip-inner.sh
python3 /opt/toddy-build/scripts/build/stage_package.py gzip 1.14-1 \
 "$LFS/sources/stage/gzip" --depends 'glibc (>= 2.44-1)' --source gzip-1.14.tar.xz \
 --recipe /opt/toddy-build/scripts/build/h07/gzip.sh --install
