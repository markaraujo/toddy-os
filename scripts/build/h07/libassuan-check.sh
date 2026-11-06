#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
[[ $(dpkg-query --admindir="$LFS/var/lib/dpkg" -W -f='${Status}' libassuan) == 'install ok installed' ]]
chroot_run <<'INNER'
set -euo pipefail
cat > /tmp/toddy-assuan.c <<'C'
#include <assuan.h>
int main(void) {assuan_context_t context;if(!assuan_check_version("3.0.2") || assuan_new(&context))return 1;assuan_release(context);return 0;}
C
cc /tmp/toddy-assuan.c $(pkg-config --cflags --libs libassuan) -o /tmp/toddy-assuan
/tmp/toddy-assuan
rm /tmp/toddy-assuan{,.c}
INNER
