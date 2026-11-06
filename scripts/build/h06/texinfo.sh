#!/bin/bash
# LFS 13.1-systemd chapter 7: texinfo; guest-root wrapper.
source /opt/toddy-build/scripts/build/h06/common.sh
cd "$LFS/sources"
python3 "$SOURCE_TOOL" texinfo-7.3.tar.xz
chroot_run < /opt/toddy-build/scripts/build/h06/texinfo-inner.sh
rm -rf "$LFS/sources/texinfo-7.3"
