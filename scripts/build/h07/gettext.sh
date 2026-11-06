#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
cd "$LFS/sources"
python3 "$SOURCE_TOOL" gettext-1.0.tar.xz
chroot_run < /opt/toddy-build/scripts/build/h07/gettext-inner.sh
python3 /opt/toddy-build/scripts/build/stage_package.py gettext 1.0-1 \
 "$LFS/sources/stage/gettext" --depends 'glibc (>= 2.44-1), gcc-runtime, ncurses' --source gettext-1.0.tar.xz \
 --recipe /opt/toddy-build/scripts/build/h07/gettext.sh --install
