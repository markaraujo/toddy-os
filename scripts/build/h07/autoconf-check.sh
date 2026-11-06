#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
[[ $(dpkg-query --admindir="$LFS/var/lib/dpkg" -W -f='${Status}' autoconf) == 'install ok installed' ]]
chroot_run <<'INNER'
set -euo pipefail
mkdir /tmp/toddy-autoconf
cd /tmp/toddy-autoconf
printf 'AC_INIT([toddy-check],[1])\nAC_OUTPUT\n' > configure.ac
autoconf
./configure
cd /
rm -rf /tmp/toddy-autoconf
INNER
