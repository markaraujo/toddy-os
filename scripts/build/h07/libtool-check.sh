#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
[[ $(dpkg-query --admindir="$LFS/var/lib/dpkg" -W -f='${Status}' libtool) == 'install ok installed' ]]
chroot_run <<'INNER'
set -euo pipefail
libtool --version | grep -F '2.6.2'
cat > /tmp/toddy-ltdl.c <<'C'
#include <ltdl.h>
int main(void) { if (lt_dlinit()) return 1; lt_dlhandle h=lt_dlopen("libc.so.6"); if(!h) return 2; if(!lt_dlsym(h,"printf")) return 3; lt_dlclose(h); return lt_dlexit(); }
C
cc /tmp/toddy-ltdl.c -lltdl -o /tmp/toddy-ltdl
/tmp/toddy-ltdl
rm /tmp/toddy-ltdl{,.c}
INNER
