#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
cd "$LFS/sources"
python3 "$SOURCE_TOOL" groff-1.24.1.tar.gz
chroot_run < /opt/toddy-build/scripts/build/h07/groff-inner.sh
python3 /opt/toddy-build/scripts/build/stage_package.py groff 1.24.1-1 \
 "$LFS/sources/stage/groff" --depends 'glibc (>= 2.44-1), gcc-runtime, perl' --source groff-1.24.1.tar.gz \
 --recipe /opt/toddy-build/scripts/build/h07/groff.sh --install
