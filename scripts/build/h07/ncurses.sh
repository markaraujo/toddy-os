#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
cd "$LFS/sources"
python3 "$SOURCE_TOOL" ncurses-6.6.tar.gz
chroot_run < /opt/toddy-build/scripts/build/h07/ncurses-inner.sh
python3 /opt/toddy-build/scripts/build/stage_package.py ncurses 6.6-1 \
 "$LFS/sources/stage/ncurses" --depends 'glibc (>= 2.44-1), gcc-runtime' --source ncurses-6.6.tar.gz \
 --recipe /opt/toddy-build/scripts/build/h07/ncurses.sh --install
