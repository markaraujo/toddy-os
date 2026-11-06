#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
[[ $(dpkg-query --admindir="$LFS/var/lib/dpkg" -W -f='${Status}' gperf) == 'install ok installed' ]]
chroot_run <<'INNER'
set -euo pipefail
printf 'native\npackage\n' | gperf > /tmp/toddy-hash.c
cc -c /tmp/toddy-hash.c -o /tmp/toddy-hash.o
rm /tmp/toddy-hash.{c,o}
INNER
