#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
cd "$LFS/sources"
python3 "$SOURCE_TOOL" bison-3.8.2.tar.xz
chroot_run < /opt/toddy-build/scripts/build/h07/bison-inner.sh
python3 /opt/toddy-build/scripts/build/stage_package.py bison 3.8.2-1 \
 "$LFS/sources/stage/bison" --depends 'glibc (>= 2.44-1), m4' --source bison-3.8.2.tar.xz \
 --recipe /opt/toddy-build/scripts/build/h07/bison.sh --install
