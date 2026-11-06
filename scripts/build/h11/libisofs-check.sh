#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
python3 /opt/toddy-build/scripts/build/h11/require_gate.py
chroot_run <<'INNER'
set -euo pipefail
[[ $(dpkg-query -W -f='${Status} ${Version}' libisofs) == 'install ok installed 1.5.8.pl02-1' ]]
[[ $(pkg-config --modversion libisofs-1) == 1.5.8 ]]
dpkg-query -S /usr/lib/libisofs.so /usr/include/libisofs/libisofs.h
fixture=$(mktemp -d /tmp/toddy-libisofs.XXXXXX)
trap 'rm -rf "$fixture"' EXIT
cat > "$fixture/probe.c" <<'C'
#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
#include <unistd.h>
#include <sys/types.h>
#include <libisofs/libisofs.h>
int main(void) {
 int major=0, minor=0, micro=0;
 iso_lib_version(&major, &minor, &micro);
 printf("libisofs native runtime %d.%d.%d\n", major, minor, micro);
 if (major != 1 || minor != 5 || micro != 8) return 1;
 if (iso_init() != 1) return 2; iso_finish();
 return 0;
}
C
cc $(pkg-config --cflags libisofs-1) "$fixture/probe.c" -o "$fixture/probe" $(pkg-config --libs libisofs-1)
"$fixture/probe"
INNER
