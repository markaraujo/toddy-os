#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
[[ $(dpkg-query --admindir="$LFS/var/lib/dpkg" -W -f='${Status}' psmisc) == 'install ok installed' ]]
chroot "$LFS" /usr/bin/killall --version 2>&1 | grep -F 23.7
chroot_run <<'INNER'
set -euo pipefail
pstree -p $$
killall -l | grep -F TERM
INNER
