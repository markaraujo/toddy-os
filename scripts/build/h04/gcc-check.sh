#!/bin/bash
source /opt/toddy-build/scripts/build/h04/common.sh
[[ $("$LFS_TGT-gcc" -dumpmachine) == "$LFS_TGT" ]]
[[ $("$LFS_TGT-gcc" -dumpfullversion) == 16.2.0 ]]
[[ $("$LFS_TGT-gcc" -print-sysroot) == "$LFS" ]]
[[ $("$LFS_TGT-gcc" -print-prog-name=ld) == "$LFS"/* ]]
"$LFS_TGT-gcc" -v
printf 'int cross_object(void) { return 42; }\n' | "$LFS_TGT-gcc" -x c -c -o /tmp/toddy-cross-object.o -
"$LFS_TGT-readelf" -h /tmp/toddy-cross-object.o | grep 'Advanced Micro Devices X86-64'
rm /tmp/toddy-cross-object.o
