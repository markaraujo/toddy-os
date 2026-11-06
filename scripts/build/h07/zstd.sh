#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
cd "$LFS/sources"
python3 "$SOURCE_TOOL" zstd-1.5.7.tar.gz
chroot_run < /opt/toddy-build/scripts/build/h07/zstd-inner.sh
python3 /opt/toddy-build/scripts/build/stage_package.py zstd 1.5.7-1 \
    "$LFS/sources/stage/zstd" --depends 'glibc (>= 2.44-1), zlib, lz4, xz' --source zstd-1.5.7.tar.gz \
    --recipe /opt/toddy-build/scripts/build/h07/zstd.sh --install
rm -rf "$LFS/sources/zstd-1.5.7"
