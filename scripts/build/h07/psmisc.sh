#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
cd "$LFS/sources"
python3 "$SOURCE_TOOL" psmisc-23.7.tar.xz
chroot_run < /opt/toddy-build/scripts/build/h07/psmisc-inner.sh
python3 /opt/toddy-build/scripts/build/stage_package.py psmisc 23.7-1 \
 "$LFS/sources/stage/psmisc" --depends 'glibc (>= 2.44-1), ncurses' --source psmisc-23.7.tar.xz \
 --recipe /opt/toddy-build/scripts/build/h07/psmisc.sh --install
