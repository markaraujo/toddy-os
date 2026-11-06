#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
cd "$LFS/sources"
python3 "$SOURCE_TOOL" autoconf-2.73.tar.xz
chroot_run < /opt/toddy-build/scripts/build/h07/autoconf-inner.sh
python3 /opt/toddy-build/scripts/build/stage_package.py autoconf 2.73-1 \
 "$LFS/sources/stage/autoconf" --depends 'perl, m4, bash' --source autoconf-2.73.tar.xz \
 --recipe /opt/toddy-build/scripts/build/h07/autoconf.sh --install
