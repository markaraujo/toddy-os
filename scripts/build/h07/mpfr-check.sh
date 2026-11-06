#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
[[ $(dpkg-query --admindir="$LFS/var/lib/dpkg" -W -f='${Status}' mpfr) == 'install ok installed' ]]
test -s "$LFS/sources/evidence/h07-mpfr/test-reports.tar.gz"
chroot_run <<'INNER'
set -euo pipefail
pkg-config --modversion mpfr | grep -Fx '4.2.2'
INNER
