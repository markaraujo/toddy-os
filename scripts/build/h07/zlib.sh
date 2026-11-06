#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
cd "$LFS/sources"
python3 "$SOURCE_TOOL" zlib-1.3.2.tar.gz
chroot_run < /opt/toddy-build/scripts/build/h07/zlib-inner.sh
python3 /opt/toddy-build/scripts/build/stage_package.py zlib 1.3.2-1 \
    "$LFS/sources/stage/zlib" --depends 'glibc (>= 2.44-1)' --source zlib-1.3.2.tar.gz \
    --recipe /opt/toddy-build/scripts/build/h07/zlib.sh --install
rm -rf "$LFS/sources/zlib-1.3.2"
