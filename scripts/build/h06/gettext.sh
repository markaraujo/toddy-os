#!/bin/bash
# LFS 13.1-systemd chapter 7: gettext; guest-root wrapper.
source /opt/toddy-build/scripts/build/h06/common.sh
cd "$LFS/sources"
python3 "$SOURCE_TOOL" gettext-1.0.tar.xz
chroot_run < /opt/toddy-build/scripts/build/h06/gettext-inner.sh
rm -rf "$LFS/sources/gettext-1.0"
