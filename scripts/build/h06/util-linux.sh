#!/bin/bash
# LFS 13.1-systemd chapter 7: util-linux; guest-root wrapper.
source /opt/toddy-build/scripts/build/h06/common.sh
cd "$LFS/sources"
python3 "$SOURCE_TOOL" util-linux-2.42.2.tar.xz
chroot_run < /opt/toddy-build/scripts/build/h06/util-linux-inner.sh
rm -rf "$LFS/sources/util-linux-2.42.2"
