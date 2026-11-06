#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
cd "$LFS/sources"
python3 "$SOURCE_TOOL" grep-3.12.tar.xz
chroot_run < /opt/toddy-build/scripts/build/h07/grep-inner.sh
python3 /opt/toddy-build/scripts/build/stage_package.py grep 3.12-1 \
 "$LFS/sources/stage/grep" --depends 'glibc (>= 2.44-1), pcre2' --source grep-3.12.tar.xz \
 --recipe /opt/toddy-build/scripts/build/h07/grep.sh --install
