#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
[[ $(dpkg-query --admindir="$LFS/var/lib/dpkg" -W -f='${Status}' pkgconf) == 'install ok installed' ]]
chroot_run <<'INNER'
set -euo pipefail
pkg-config --version | grep -Fx '3.0.5'
pkg-config --modversion zlib | grep -Fx '1.3.2'
pkg-config --libs liblzma
INNER
