#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
cd "$LFS/sources"
python3 "$SOURCE_TOOL" glibc-2.44.tar.xz
python3 "$SOURCE_TOOL" --verify-only glibc-fhs-1.patch
python3 "$SOURCE_TOOL" --verify-only glibc-2.44-upstream_fixes-3.patch
chroot_run < /opt/toddy-build/scripts/build/h07/glibc-build-inner.sh
python3 /opt/toddy-build/scripts/build/h07/evaluate-glibc.py
