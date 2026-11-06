#!/bin/bash
# Frozen LFS 13.1-systemd, 5.4.
source /opt/toddy-build/scripts/build/h04/common.sh
unpack linux-7.1.8.tar.xz
cd linux-7.1.8
make mrproper
make headers
find usr/include -type f ! -name '*.h' -delete
cp -rv usr/include "$LFS/usr"
cd "$LFS/sources"
rm -rf linux-7.1.8
