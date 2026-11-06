#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
python3 /opt/toddy-build/scripts/build/h11/require_gate.py
chroot_run <<'INNER'
set -euo pipefail
[[ $(dpkg-query -W -f='${Status} ${Version}' libburn) == 'install ok installed 1.5.8-1' ]]
[[ $(pkg-config --modversion libburn-1) == 1.5.8 ]]
dpkg-query -S /usr/lib/libburn.so /usr/include/libburn/libburn.h
fixture=$(mktemp -d /tmp/toddy-libburn.XXXXXX)
trap 'rm -rf "$fixture"' EXIT
cat > "$fixture/probe.c" <<'C'
#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
#include <unistd.h>
#include <sys/types.h>
#include <libburn/libburn.h>
int main(void) {
 int major=0, minor=0, micro=0;
 burn_version(&major, &minor, &micro);
 printf("libburn native runtime %d.%d.%d\n", major, minor, micro);
 if (major != 1 || minor != 5 || micro != 8) return 1;

 return 0;
}
C
cc $(pkg-config --cflags libburn-1) "$fixture/probe.c" -o "$fixture/probe" $(pkg-config --libs libburn-1)
"$fixture/probe"
INNER
