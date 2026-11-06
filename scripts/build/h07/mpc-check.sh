#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
[[ $(dpkg-query --admindir="$LFS/var/lib/dpkg" -W -f='${Status}' mpc) == 'install ok installed' ]]
test -s "$LFS/sources/evidence/h07-mpc/test-reports.tar.gz"
chroot_run <<'INNER'
set -euo pipefail
pkg-config --modversion mpc | grep -Fx '1.4.1'
INNER
