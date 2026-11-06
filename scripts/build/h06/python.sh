#!/bin/bash
# LFS 13.1-systemd chapter 7: Python; guest-root wrapper.
source /opt/toddy-build/scripts/build/h06/common.sh
cd "$LFS/sources"
python3 "$SOURCE_TOOL" Python-3.14.7.tar.xz
chroot_run < /opt/toddy-build/scripts/build/h06/python-inner.sh
rm -rf "$LFS/sources/Python-3.14.7"
