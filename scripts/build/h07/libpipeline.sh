#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
cd "$LFS/sources"
python3 "$SOURCE_TOOL" libpipeline-1.5.8.tar.gz
chroot_run < /opt/toddy-build/scripts/build/h07/libpipeline-inner.sh
python3 /opt/toddy-build/scripts/build/stage_package.py libpipeline 1.5.8-1 \
 "$LFS/sources/stage/libpipeline" --depends 'glibc (>= 2.44-1)' --source libpipeline-1.5.8.tar.gz \
 --recipe /opt/toddy-build/scripts/build/h07/libpipeline.sh --install
