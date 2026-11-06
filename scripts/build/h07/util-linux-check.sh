#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
[[ $(dpkg-query --admindir="$LFS/var/lib/dpkg" -W -f='${Status}' util-linux) == 'install ok installed' ]]
chroot_run <<'INNER'
set -euo pipefail
findmnt --version | grep -F '2.42.4'
[[ $(findmnt -n -o FSTYPE /proc) == proc ]]
uuidgen | grep -E '^[0-9a-f]{8}(-[0-9a-f]{4}){3}-[0-9a-f]{12}$'
INNER
