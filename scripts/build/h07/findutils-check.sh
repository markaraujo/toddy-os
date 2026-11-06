#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
[[ $(dpkg-query --admindir="$LFS/var/lib/dpkg" -W -f='${Status}' findutils) == 'install ok installed' ]]
chroot_run <<'INNER'
set -euo pipefail
mkdir /tmp/toddy-find
printf native > /tmp/toddy-find/item
[[ $(find /tmp/toddy-find -type f -print) == /tmp/toddy-find/item ]]
find /tmp/toddy-find -type f -print0 | xargs -0 cat | grep -Fx native
rm -r /tmp/toddy-find
INNER
