#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
cd "$LFS/sources"
python3 "$SOURCE_TOOL" tcl8.6.18-src.tar.gz
python3 "$SOURCE_TOOL" --verify-only tcl8.6.18-html.tar.gz
chroot_run < /opt/toddy-build/scripts/build/h07/tcl-inner.sh
python3 /opt/toddy-build/scripts/build/stage_package.py tcl 8.6.18-1 \
    "$LFS/sources/stage/tcl" --depends 'glibc (>= 2.44-1), zlib' \
    --source tcl8.6.18-src.tar.gz --source tcl8.6.18-html.tar.gz \
    --recipe /opt/toddy-build/scripts/build/h07/tcl.sh --install
rm -rf "$LFS/sources/tcl8.6.18"
