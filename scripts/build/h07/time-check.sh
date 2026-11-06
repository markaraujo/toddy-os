#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
[[ $(dpkg-query --admindir="$LFS/var/lib/dpkg" -W -f='${Status}' time) == 'install ok installed' ]]
chroot_run <<'INNER'
set -euo pipefail
/usr/bin/time --version | grep -F '1.10'
set +e
/usr/bin/time -f 'TODDY_TIME %x %e %M' -o /tmp/toddy-time-result sh -c 'exit 7'
result=$?
set -e
[[ $result == 7 ]]
grep -E '^TODDY_TIME 7 [0-9]+\.[0-9]+ [0-9]+$' /tmp/toddy-time-result
rm /tmp/toddy-time-result
INNER
