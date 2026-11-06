#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
[[ $(dpkg-query --admindir="$LFS/var/lib/dpkg" -W -f='${Status}' kmod) == 'install ok installed' ]]
chroot_run <<'INNER'
set -euo pipefail
kmod --version | grep -F '34.2'
lsmod > /tmp/toddy-lsmod.txt
head /tmp/toddy-lsmod.txt
rm /tmp/toddy-lsmod.txt
# No target-kernel module insertion is claimed before H09 native boot.

INNER
