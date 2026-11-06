#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
cd "$LFS/sources"
python3 "$SOURCE_TOOL" readline-8.3.tar.gz
chroot_run < /opt/toddy-build/scripts/build/h07/readline-inner.sh
python3 /opt/toddy-build/scripts/build/stage_package.py readline 8.3-1 \
    "$LFS/sources/stage/readline" --depends 'glibc (>= 2.44-1)' --source readline-8.3.tar.gz \
    --recipe /opt/toddy-build/scripts/build/h07/readline.sh --install
rm -rf "$LFS/sources/readline-8.3"
