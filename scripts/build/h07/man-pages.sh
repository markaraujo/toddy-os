#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
cd "$LFS/sources"
[[ ! -e stage/man-pages ]] || { echo 'Inspect existing stage before retry'; exit 1; }
python3 "$SOURCE_TOOL" man-pages-6.18.tar.xz
chroot_run < /opt/toddy-build/scripts/build/h07/man-pages-inner.sh
python3 /opt/toddy-build/scripts/build/stage_package.py man-pages 6.18-1 \
    "$LFS/sources/stage/man-pages" --architecture all --source man-pages-6.18.tar.xz \
    --recipe /opt/toddy-build/scripts/build/h07/man-pages.sh --install
rm -rf "$LFS/sources/man-pages-6.18"
