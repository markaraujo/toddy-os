#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
cd "$LFS/sources"
python3 "$SOURCE_TOOL" expat-2.10.0.tar.xz
chroot_run < /opt/toddy-build/scripts/build/h07/expat-inner.sh
python3 /opt/toddy-build/scripts/build/stage_package.py expat 2.10.0-1 \
 "$LFS/sources/stage/expat" --depends 'glibc (>= 2.44-1)' --source expat-2.10.0.tar.xz \
 --recipe /opt/toddy-build/scripts/build/h07/expat.sh --install
