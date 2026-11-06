#!/bin/bash
# LFS 13.1-systemd chapter 7: bison; guest-root wrapper.
source /opt/toddy-build/scripts/build/h06/common.sh
cd "$LFS/sources"
python3 "$SOURCE_TOOL" bison-3.8.2.tar.xz
chroot_run < /opt/toddy-build/scripts/build/h06/bison-inner.sh
rm -rf "$LFS/sources/bison-3.8.2"
