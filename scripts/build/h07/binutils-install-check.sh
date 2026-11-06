#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
[[ $(dpkg-query --admindir="$LFS/var/lib/dpkg" -W -f='${Status}' binutils) == 'install ok installed' ]]
chroot_run <<'INNER'
set -euo pipefail
ld --version | grep -F '2.47'
as --version | grep -F '2.47'
ld --verbose | grep -F 'SEARCH_DIR' | tee /tmp/toddy-ld-search
! grep -E '/tools|/mnt/lfs|/usr/lib64' /tmp/toddy-ld-search
printf 'int main(void) { return 0; }\n' > /tmp/toddy-binutils.c
gcc /tmp/toddy-binutils.c -o /tmp/toddy-binutils
/tmp/toddy-binutils
readelf -l /tmp/toddy-binutils | grep -F '/lib64/ld-linux-x86-64.so.2'
rm /tmp/toddy-binutils{,.c} /tmp/toddy-ld-search
INNER
