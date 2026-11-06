#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
cd "$LFS/sources"
python3 "$SOURCE_TOOL" sed-4.10.tar.xz
chroot_run < /opt/toddy-build/scripts/build/h07/sed-inner.sh
python3 /opt/toddy-build/scripts/build/stage_package.py sed 4.10-1 \
 "$LFS/sources/stage/sed" --depends 'glibc (>= 2.44-1)' --source sed-4.10.tar.xz \
 --recipe /opt/toddy-build/scripts/build/h07/sed.sh --install
