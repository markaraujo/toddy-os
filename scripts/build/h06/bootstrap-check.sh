#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
[[ $(findmnt -n -o FSTYPE --mountpoint "$LFS/proc") == proc ]]
[[ $(findmnt -n -o FSTYPE --mountpoint "$LFS/sys") == sysfs ]]
[[ $(findmnt -n -o FSTYPE --mountpoint "$LFS/dev/pts") == devpts ]]
chroot_run <<'INNER'
set -euo pipefail
[[ $PATH == /usr/bin:/usr/sbin ]]
[[ $(id -un) == root ]]
[[ ! -e /usr/lib64 ]]
[[ $(gcc -dumpmachine) == x86_64-lfs-linux-gnu ]]
printf '#include <stdio.h>\nint main(void){puts("Native chroot C works");}\n' > /tmp/toddy-native.c
gcc /tmp/toddy-native.c -o /tmp/toddy-native
/tmp/toddy-native | grep -Fx 'Native chroot C works'
printf '#include <iostream>\nint main(){std::cout << "Native chroot C++ works\\n";}\n' > /tmp/toddy-native.cc
g++ /tmp/toddy-native.cc -o /tmp/toddy-native-cxx
/tmp/toddy-native-cxx | grep -Fx 'Native chroot C++ works'
readelf -l /tmp/toddy-native | grep '/lib64/ld-linux-x86-64.so.2'
! gcc -print-search-dirs | grep -E '/mnt/lfs|/tools'
ldd /tmp/toddy-native
rm /tmp/toddy-native{,.c,.cc,-cxx}
env | sort
INNER
