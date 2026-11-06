#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
[[ $(dpkg-query --admindir="$LFS/var/lib/dpkg" -W -f='${Status}' readline) == 'install ok installed' ]]
chroot_run <<'INNER'
set -euo pipefail
printf '#include <stdio.h>\n#include <readline/readline.h>\nint main(void){puts(rl_library_version);}\n' > /tmp/toddy-readline.c
gcc /tmp/toddy-readline.c -o /tmp/toddy-readline -lreadline -lncursesw
/tmp/toddy-readline | grep -Fx '8.3'
rm /tmp/toddy-readline{,.c}
INNER
