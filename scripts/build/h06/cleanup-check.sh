#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
[[ ! -e $LFS/tools ]]
chroot_run <<'INNER'
set -euo pipefail
printf '#include <stdio.h>\nint main(void){puts("Self-hosting after tools removal");}\n' > /tmp/toddy-clean.c
gcc /tmp/toddy-clean.c -o /tmp/toddy-clean
/tmp/toddy-clean | grep -Fx 'Self-hosting after tools removal'
! gcc -print-search-dirs | grep -E '/mnt/lfs|/tools'
python3 --version
perl -e 'print "Perl after tools removal works\n"'
rm /tmp/toddy-clean{,.c}
INNER
