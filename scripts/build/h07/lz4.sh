#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
cd "$LFS/sources"
python3 "$SOURCE_TOOL" lz4-1.10.0.tar.gz
chroot_run < /opt/toddy-build/scripts/build/h07/lz4-inner.sh
python3 /opt/toddy-build/scripts/build/stage_package.py lz4 1.10.0-1 \
    "$LFS/sources/stage/lz4" --depends 'glibc (>= 2.44-1)' --source lz4-1.10.0.tar.gz \
    --recipe /opt/toddy-build/scripts/build/h07/lz4.sh --install
rm -rf "$LFS/sources/lz4-1.10.0"
