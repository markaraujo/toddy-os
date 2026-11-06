#!/bin/bash
source /opt/toddy-build/scripts/build/h05/check-common.sh
[[ $(readlink "$LFS/usr/bin/cc") == gcc ]]
test -f "$LFS/usr/lib/libgcc_s.so.1"
test -f "$LFS/usr/lib/libstdc++.so.6"
"$LFS_TGT-readelf" -l "$LFS/usr/bin/gcc" | grep 'interpreter: /lib64/ld-linux-x86-64.so.2'
! "$LFS_TGT-readelf" -d "$LFS/usr/bin/gcc" | grep -E '\((RPATH|RUNPATH)\)'
# A native compiler must run in chroot; do not run it against builder libraries.
# H06 supplies actual native C/C++ compilation and runtime checks.
