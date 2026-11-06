#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
cd "$LFS/sources"
python3 "$SOURCE_TOOL" npth-1.8.tar.bz2
chroot_run < /opt/toddy-build/scripts/build/h07/npth-inner.sh
python3 /opt/toddy-build/scripts/build/stage_package.py npth 1.8-1 \
 "$LFS/sources/stage/npth" --depends 'glibc (>= 2.44-1)' --source npth-1.8.tar.bz2 \
 --recipe /opt/toddy-build/scripts/build/h07/npth.sh --install
