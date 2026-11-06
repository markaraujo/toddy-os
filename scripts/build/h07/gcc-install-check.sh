#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
for package in gcc gcc-runtime; do
 [[ $(dpkg-query --admindir="$LFS/var/lib/dpkg" -W -f='${Version} ${Status}' "$package") == '16.2.0-1 install ok installed' ]]
done
chroot_run <<'INNER'
set -euo pipefail
gcc --version | grep -F '16.2.0'
[[ $(gcc -dumpmachine) == x86_64-pc-linux-gnu ]]
mkdir -p /sources/evidence/h07-gcc
cd /sources/evidence/h07-gcc
printf 'int main(void) { return 0; }\n' | cc -x c - -v -Wl,--verbose -o native-c > native-sanity.log 2>&1
./native-c
readelf -l native-c | grep -F '/lib64/ld-linux-x86-64.so.2'
[[ $(grep -E '/usr/lib.*/(S?crt1|crti|crtn)\.o succeeded' native-sanity.log | wc -l) == 3 ]]
grep -B4 '^ /usr/include' native-sanity.log
grep -F 'attempt to open /usr/lib/libc.so.6 succeeded' native-sanity.log
grep -F 'found ld-linux-x86-64.so.2 at /usr/lib/ld-linux-x86-64.so.2' native-sanity.log
! grep -E '/tools|/mnt/lfs|x86_64-lfs-linux-gnu|/usr/lib64' native-sanity.log
! readelf -d native-c | grep -E 'RPATH|RUNPATH'
cat > native-cxx.cc <<'CXX'
#include <iostream>
#include <thread>
int main() { std::thread worker([]{}); worker.join(); std::cout << "GCC_NATIVE_OK\n"; }
CXX
g++ -pthread native-cxx.cc -o native-cxx
./native-cxx | grep -Fx GCC_NATIVE_OK
[[ $(gcc -print-file-name=include) == /usr/lib/gcc/x86_64-pc-linux-gnu/16.2.0/include ]]
[[ $(stat -c '%U:%G' "$(gcc -print-file-name=include)") == root:root ]]
INNER
