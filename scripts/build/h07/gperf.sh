#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
cd "$LFS/sources"
python3 "$SOURCE_TOOL" gperf-3.3.tar.gz
chroot_run < /opt/toddy-build/scripts/build/h07/gperf-inner.sh
python3 /opt/toddy-build/scripts/build/stage_package.py gperf 3.3-1 \
 "$LFS/sources/stage/gperf" --depends 'glibc (>= 2.44-1), gcc-runtime' --source gperf-3.3.tar.gz \
 --recipe /opt/toddy-build/scripts/build/h07/gperf.sh --install
