#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
cd "$LFS/sources"
python3 "$SOURCE_TOOL" dbus-1.16.2.tar.xz
chroot_run < /opt/toddy-build/scripts/build/h07/dbus-inner.sh
python3 /opt/toddy-build/scripts/build/stage_package.py dbus 1.16.2-1 \
 "$LFS/sources/stage/dbus" --depends 'glibc (>= 2.44-1), expat, systemd' --source dbus-1.16.2.tar.xz  \
 --recipe /opt/toddy-build/scripts/build/h07/dbus.sh --install
