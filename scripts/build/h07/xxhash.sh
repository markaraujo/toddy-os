#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
cd "$LFS/sources"
python3 "$SOURCE_TOOL" xxHash-0.8.4.tar.gz
chroot_run < /opt/toddy-build/scripts/build/h07/xxhash-inner.sh
python3 /opt/toddy-build/scripts/build/stage_package.py xxhash 0.8.4-1 \
 "$LFS/sources/stage/xxhash" --depends 'glibc (>= 2.44-1)' --source xxHash-0.8.4.tar.gz \
 --recipe /opt/toddy-build/scripts/build/h07/xxhash.sh --install
