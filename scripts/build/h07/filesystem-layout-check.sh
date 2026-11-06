#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
chroot_run <<'INNER'
set -euo pipefail
[[ $(readlink /bin) == usr/bin && $(readlink /lib) == usr/lib && $(readlink /sbin) == usr/sbin ]]
[[ $(readlink /usr/bin/sh) == bash ]]
[[ $(readlink /etc/mtab) == /proc/self/mounts ]]
[[ $(readlink /var/run) == /run && $(readlink /var/lock) == /run/lock ]]
dpkg-query -S /lib64/ld-linux-x86-64.so.2 /usr/bin/sh | grep -F filesystem-layout
sh -c 'test "$((6 * 7))" = 42'
/lib64/ld-linux-x86-64.so.2 --list /usr/bin/bash
INNER
