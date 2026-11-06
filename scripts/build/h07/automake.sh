#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
cd "$LFS/sources"
python3 "$SOURCE_TOOL" automake-1.18.1.tar.xz
chroot_run < /opt/toddy-build/scripts/build/h07/automake-inner.sh
python3 /opt/toddy-build/scripts/build/stage_package.py automake 1.18.1-1 \
 "$LFS/sources/stage/automake" --depends 'perl, autoconf, bash' --source automake-1.18.1.tar.xz \
 --recipe /opt/toddy-build/scripts/build/h07/automake.sh --install
