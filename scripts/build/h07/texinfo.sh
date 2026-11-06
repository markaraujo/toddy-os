#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
cd "$LFS/sources"
python3 "$SOURCE_TOOL" texinfo-7.3.tar.xz
chroot_run < /opt/toddy-build/scripts/build/h07/texinfo-inner.sh
python3 /opt/toddy-build/scripts/build/stage_package.py texinfo 7.3-1 \
 "$LFS/sources/stage/texinfo" --depends 'glibc (>= 2.44-1), perl, ncurses' --source texinfo-7.3.tar.xz \
 --recipe /opt/toddy-build/scripts/build/h07/texinfo.sh --install
