#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
cd "$LFS/sources"
python3 "$SOURCE_TOOL" less-704.tar.gz
chroot_run < /opt/toddy-build/scripts/build/h07/less-inner.sh
python3 /opt/toddy-build/scripts/build/stage_package.py less 704-1 \
 "$LFS/sources/stage/less" --depends 'glibc (>= 2.44-1), ncurses' --source less-704.tar.gz \
 --recipe /opt/toddy-build/scripts/build/h07/less.sh --install
