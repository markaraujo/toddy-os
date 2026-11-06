#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
[[ $(dpkg-query --admindir="$LFS/var/lib/dpkg" -W -f='${Status}' inetutils) == 'install ok installed' ]]
chroot_run <<'INNER'
set -euo pipefail
ifconfig lo | grep -F 'LOOPBACK'
ping -c 1 127.0.0.1
hostname | grep .
test ! -e /usr/sbin/telnetd
INNER
