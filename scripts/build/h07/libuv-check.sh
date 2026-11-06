#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
[[ $(dpkg-query --admindir="$LFS/var/lib/dpkg" -W -f='${Status}' libuv) == 'install ok installed' ]]
chroot_run <<'INNER'
set -euo pipefail
cat > /tmp/toddy-uv.c <<'C'
#include <uv.h>
#include <string.h>
int main(void) {uv_loop_t l; if(strcmp(uv_version_string(),"1.52.1")) return 1; if(uv_loop_init(&l)) return 2; uv_run(&l, UV_RUN_DEFAULT); return uv_loop_close(&l);}
C
cc /tmp/toddy-uv.c -luv -o /tmp/toddy-uv
/tmp/toddy-uv
rm /tmp/toddy-uv{,.c}
INNER
