#!/bin/bash
source /opt/toddy-build/scripts/build/h05/check-common.sh
test -f "$LFS/usr/lib/libncursesw.so"
[[ $(readlink "$LFS/usr/lib/libncurses.so") == libncursesw.so ]]
test -f "$LFS/usr/include/curses.h"
"$LFS/tools/bin/tic" -V | grep '6.6'
"$LFS_TGT-readelf" -d "$LFS/usr/lib/libncursesw.so" | grep SONAME
