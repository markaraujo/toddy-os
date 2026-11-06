#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
cd "$LFS/sources"
python3 "$SOURCE_TOOL" file-5.48.tar.gz
chroot_run < /opt/toddy-build/scripts/build/h07/file-inner.sh
python3 /opt/toddy-build/scripts/build/stage_package.py file 5.48-1 \
    "$LFS/sources/stage/file" --depends 'glibc (>= 2.44-1), zlib, bzip2, xz, zstd, lz4' --source file-5.48.tar.gz \
    --recipe /opt/toddy-build/scripts/build/h07/file.sh --install
rm -rf "$LFS/sources/file-5.48"
