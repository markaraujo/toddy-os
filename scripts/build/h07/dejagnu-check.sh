#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
[[ $(dpkg-query --admindir="$LFS/var/lib/dpkg" -W -f='${Status}' dejagnu) == 'install ok installed' ]]
chroot_run <<'INNER'
set -euo pipefail
runtest --version | grep '1.6.3'
INNER
