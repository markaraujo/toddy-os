#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
[[ $(dpkg-query --admindir="$LFS/var/lib/dpkg" -W -f='${Status}' procps-ng) == 'install ok installed' ]]
chroot_run <<'INNER'
set -euo pipefail
ps --version | grep -F '4.0.7'
ps -p $$ -o pid= | grep -E '[0-9]'
free -b | grep -F Mem:
INNER
