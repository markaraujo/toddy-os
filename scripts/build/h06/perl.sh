#!/bin/bash
# LFS 13.1-systemd chapter 7: perl; guest-root wrapper.
source /opt/toddy-build/scripts/build/h06/common.sh
cd "$LFS/sources"
python3 "$SOURCE_TOOL" perl-5.44.0.tar.xz
chroot_run < /opt/toddy-build/scripts/build/h06/perl-inner.sh
rm -rf "$LFS/sources/perl-5.44.0"
