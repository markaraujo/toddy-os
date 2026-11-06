#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
[[ $(dpkg-query --admindir="$LFS/var/lib/dpkg" -W -f='${Status}' xz) == 'install ok installed' ]]
chroot_run <<'INNER'
set -euo pipefail
xz --version | grep '5.8.4'
printf 'Native xz roundtrip\n' | xz -c | xz -dc | grep -Fx 'Native xz roundtrip'
INNER
