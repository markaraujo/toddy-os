#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
[[ $(dpkg-query --admindir="$LFS/var/lib/dpkg" -W -f='${Status}' file) == 'install ok installed' ]]
chroot_run <<'INNER'
set -euo pipefail
file --version | grep '5.48'
file /usr/bin/bash | grep 'ELF 64-bit'
INNER
