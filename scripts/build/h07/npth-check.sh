#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
[[ $(dpkg-query --admindir="$LFS/var/lib/dpkg" -W -f='${Status}' npth) == 'install ok installed' ]]
chroot_run <<'INNER'
set -euo pipefail
cat > /tmp/toddy-npth.c <<'C'
#include <npth.h>
static void *worker(void *v) {return v;}
int main(void) {npth_t thread;void *out=0;int marker=42;if(npth_init() || npth_create(&thread,0,worker,&marker) || npth_join(thread,&out))return 1;return out!=&marker;}
C
cc /tmp/toddy-npth.c -lnpth -pthread -o /tmp/toddy-npth
/tmp/toddy-npth
rm /tmp/toddy-npth{,.c}
INNER
