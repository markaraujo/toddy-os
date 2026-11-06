#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
[[ $(dpkg-query --admindir="$LFS/var/lib/dpkg" -W -f='${Status}' man-db) == 'install ok installed' ]]
chroot_run <<'INNER'
set -euo pipefail
man --version | grep -F '2.13.1'
MANWIDTH=80 MANPAGER=cat man -P cat 1 printf | col -b | grep -m1 -i 'format and print'
INNER
