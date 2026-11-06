#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
[[ $(dpkg-query --admindir="$LFS/var/lib/dpkg" -W -f='${Status}' less) == 'install ok installed' ]]
chroot_run <<'INNER'
set -euo pipefail
printf 'LESS_NATIVE_OK\n' | less -F -X > /tmp/toddy-less.txt
grep -Fx LESS_NATIVE_OK /tmp/toddy-less.txt
rm /tmp/toddy-less.txt
INNER
