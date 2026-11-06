#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
[[ $(dpkg-query --admindir="$LFS/var/lib/dpkg" -W -f='${Status}' e2fsprogs) == 'install ok installed' ]]
chroot_run <<'INNER'
set -euo pipefail
mke2fs -V 2>&1 | grep -F '1.47.4'
fixture=$(mktemp /tmp/toddy-ext4.XXXXXX)
trap 'rm -f "$fixture"' EXIT
truncate -s 32M "$fixture"
mke2fs -q -t ext4 -F "$fixture"
e2fsck -fn "$fixture"
dumpe2fs -h "$fixture" 2>/dev/null | grep -F 'Filesystem features:'
INNER
