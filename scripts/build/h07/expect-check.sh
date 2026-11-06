#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
[[ $(dpkg-query --admindir="$LFS/var/lib/dpkg" -W -f='${Status}' expect) == 'install ok installed' ]]
chroot_run <<'INNER'
set -euo pipefail
expect -v | grep '5.45.4'
expect -c 'spawn /usr/bin/echo EXPECT_PTY_OK; expect "EXPECT_PTY_OK"; expect eof'
INNER
