#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
cd "$LFS/sources"
python3 "$SOURCE_TOOL" grub-2.14.tar.xz
chroot_run < /opt/toddy-build/scripts/build/h07/grub-inner.sh
python3 /opt/toddy-build/scripts/build/stage_package.py grub 2.14-1 \
 "$LFS/sources/stage/grub" --depends 'glibc (>= 2.44-1), gettext, xz' --source grub-2.14.tar.xz \
 --recipe /opt/toddy-build/scripts/build/h07/grub.sh --install
