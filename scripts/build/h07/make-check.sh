#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
[[ $(dpkg-query --admindir="$LFS/var/lib/dpkg" -W -f='${Status}' make) == 'install ok installed' ]]
chroot_run <<'INNER'
set -euo pipefail
printf 'all:\n\t@printf MAKE_NATIVE_OK\\n\n' > /tmp/toddy-Makefile
make -f /tmp/toddy-Makefile | grep -F MAKE_NATIVE_OK
rm /tmp/toddy-Makefile
INNER
