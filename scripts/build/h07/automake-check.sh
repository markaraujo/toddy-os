#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
[[ $(dpkg-query --admindir="$LFS/var/lib/dpkg" -W -f='${Status}' automake) == 'install ok installed' ]]
chroot_run <<'INNER'
set -euo pipefail
automake --version | grep -F 1.18.1
mkdir /tmp/toddy-automake
cd /tmp/toddy-automake
printf 'AC_INIT([toddy-check],[1])\nAM_INIT_AUTOMAKE([foreign])\nAC_CONFIG_FILES([Makefile])\nAC_OUTPUT\n' > configure.ac
printf 'EXTRA_DIST = configure.ac\n' > Makefile.am
autoreconf -fi
./configure
make distcheck
cd /
rm -rf /tmp/toddy-automake
INNER
