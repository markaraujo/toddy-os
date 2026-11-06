#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
[[ $(dpkg-query --admindir="$LFS/var/lib/dpkg" -W -f='${Status}' glibc) == 'install ok installed' ]]
chroot_run <<'INNER'
set -euo pipefail
ldd --version | head -1 | grep '2.44'
printf '#include <stdio.h>\nint main(void){puts("Packaged final libc works");}\n' > /tmp/toddy-final-libc.c
gcc /tmp/toddy-final-libc.c -o /tmp/toddy-final-libc
/tmp/toddy-final-libc | grep -Fx 'Packaged final libc works'
ldd /tmp/toddy-final-libc
! readelf -d /tmp/toddy-final-libc | grep -E '\((RPATH|RUNPATH)\)'
getent hosts localhost
rm /tmp/toddy-final-libc{,.c}
INNER
