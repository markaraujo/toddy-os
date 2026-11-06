#!/bin/bash
source /opt/toddy-build/scripts/build/h04/common.sh
cd "$LFS/sources/evidence"
printf '#include <stdio.h>\nint main(void){puts("Toddy cross libc OK");return 0;}\n' > h04-hello.c
"$LFS_TGT-gcc" h04-hello.c -o h04-hello -v -Wl,--verbose > h04-linker.log 2>&1
"$LFS_TGT-readelf" -l h04-hello | grep ': /lib64/ld-linux-x86-64.so.2'
grep -E -o "$LFS/lib.*/S?crt[1in].*succeeded" h04-linker.log
grep -B3 "^ $LFS/usr/include" h04-linker.log
grep 'SEARCH.*/usr/lib' h04-linker.log | sed 's|; |\n|g'
grep "$LFS/usr/lib/libc.so.6 succeeded" h04-linker.log
grep "found ld-linux-x86-64.so.2 at $LFS/usr/lib/ld-linux-x86-64.so.2" h04-linker.log
# Execute with the target loader and only the target library directory.
"$LFS/usr/lib/ld-linux-x86-64.so.2" --library-path "$LFS/usr/lib" ./h04-hello | grep -Fx 'Toddy cross libc OK'

! "$LFS_TGT-readelf" -d h04-hello | grep -E '\((RPATH|RUNPATH)\)'
"$LFS/usr/lib/ld-linux-x86-64.so.2" --library-path "$LFS/usr/lib" --list ./h04-hello > h04-runtime-libraries.txt
grep "libc.so.6 => $LFS/usr/lib/libc.so.6" h04-runtime-libraries.txt
