#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
[[ $(dpkg-query --admindir="$LFS/var/lib/dpkg" -W -f='${Status}' kbd) == 'install ok installed' ]]
chroot_run <<'INNER'
set -euo pipefail
loadkeys --version | grep -F 2.10.0
loadkeys -b us > /tmp/toddy-keymap.bin
test -s /tmp/toddy-keymap.bin
rm /tmp/toddy-keymap.bin
INNER
