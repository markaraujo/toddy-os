#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
cd "$LFS/sources"
python3 "$SOURCE_TOOL" procps-ng-4.0.7.tar.xz
chroot_run < /opt/toddy-build/scripts/build/h07/procps-ng-inner.sh
python3 /opt/toddy-build/scripts/build/stage_package.py procps-ng 4.0.7-1 \
 "$LFS/sources/stage/procps-ng" --depends 'glibc (>= 2.44-1), ncurses, systemd' --source procps-ng-4.0.7.tar.xz  \
 --recipe /opt/toddy-build/scripts/build/h07/procps-ng.sh --install
