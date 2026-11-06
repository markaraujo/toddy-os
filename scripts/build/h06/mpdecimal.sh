#!/bin/bash
# LFS 13.1-systemd chapter 7: mpdecimal; guest-root wrapper.
source /opt/toddy-build/scripts/build/h06/common.sh
cd "$LFS/sources"
python3 "$SOURCE_TOOL" mpdecimal-4.0.1.tar.gz
chroot_run < /opt/toddy-build/scripts/build/h06/mpdecimal-inner.sh
rm -rf "$LFS/sources/mpdecimal-4.0.1"
