#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
cd "$LFS/sources"
python3 "$SOURCE_TOOL" bzip2-1.0.8.tar.gz
python3 "$SOURCE_TOOL" --verify-only bzip2-1.0.8-install_docs-1.patch
chroot_run < /opt/toddy-build/scripts/build/h07/bzip2-inner.sh
python3 /opt/toddy-build/scripts/build/stage_package.py bzip2 1.0.8-1 \
    "$LFS/sources/stage/bzip2" --depends 'glibc (>= 2.44-1)' \
    --source bzip2-1.0.8.tar.gz --source bzip2-1.0.8-install_docs-1.patch \
    --recipe /opt/toddy-build/scripts/build/h07/bzip2.sh --install
rm -rf "$LFS/sources/bzip2-1.0.8"
