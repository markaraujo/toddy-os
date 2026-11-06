#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
cd "$LFS/sources"
python3 "$SOURCE_TOOL" time-1.10.tar.gz
chroot_run < /opt/toddy-build/scripts/build/h07/time-inner.sh
python3 /opt/toddy-build/scripts/build/stage_package.py time 1.10-1 \
 "$LFS/sources/stage/time" --depends 'glibc (>= 2.44-1)' --source time-1.10.tar.gz \
 --recipe /opt/toddy-build/scripts/build/h07/time.sh --install
