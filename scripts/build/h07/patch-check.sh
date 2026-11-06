#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
[[ $(dpkg-query --admindir="$LFS/var/lib/dpkg" -W -f='${Status}' patch) == 'install ok installed' ]]
chroot_run <<'INNER'
set -euo pipefail
mkdir /tmp/toddy-patch
cd /tmp/toddy-patch
printf 'old\n' > item
printf '%s\n' '--- item' '+++ item' '@@ -1 +1 @@' '-old' '+PATCH_NATIVE_OK' > update.patch
patch --batch -p0 < update.patch
grep -Fx PATCH_NATIVE_OK item
cd /
rm -rf /tmp/toddy-patch
INNER
