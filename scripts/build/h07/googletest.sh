#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
cd "$LFS/sources"
python3 "$SOURCE_TOOL" googletest-1.18.0.tar.gz
chroot_run < /opt/toddy-build/scripts/build/h07/googletest-inner.sh
python3 /opt/toddy-build/scripts/build/stage_package.py googletest 1.18.0-1 \
 "$LFS/sources/stage/googletest" --depends 'glibc (>= 2.44-1), gcc-runtime' --source googletest-1.18.0.tar.gz \
 --recipe /opt/toddy-build/scripts/build/h07/googletest.sh --install
