#!/bin/bash
# LFS 13.1-systemd chapter 7: zlib; guest-root wrapper.
source /opt/toddy-build/scripts/build/h06/common.sh
cd "$LFS/sources"
python3 "$SOURCE_TOOL" zlib-1.3.2.tar.gz
chroot_run < /opt/toddy-build/scripts/build/h06/zlib-inner.sh
rm -rf "$LFS/sources/zlib-1.3.2"
