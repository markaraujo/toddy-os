#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
[[ $(dpkg-query --admindir="$LFS/var/lib/dpkg" -W -f='${Status}' gmp) == 'install ok installed' ]]
test -s "$LFS/sources/evidence/h07-gmp/test-reports.tar.gz"
chroot_run <<'INNER'
set -euo pipefail
pkg-config --modversion gmp | grep -Fx '6.3.0'
INNER
