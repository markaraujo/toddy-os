#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
python3 /opt/toddy-build/scripts/build/h10/require_media_tools.py
chroot_run <<'INNER'
set -euo pipefail
[[ $(dpkg-query -W -f='${Status} ${Version}' libisoburn) == 'install ok installed 1.5.8.pl02-1' ]]
[[ $(pkg-config --modversion libisoburn-1) == 1.5.8 ]]
dpkg-query -S /usr/lib/libisoburn.so /usr/include/libisoburn/libisoburn.h
fixture=$(mktemp -d /tmp/toddy-libisoburn.XXXXXX)
trap 'rm -rf "$fixture"' EXIT
cat > "$fixture/probe.c" <<'C'
#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
#include <unistd.h>
#include <sys/types.h>
#include <libburn/libburn.h>
#include <libisofs/libisofs.h>
#include <libisoburn/libisoburn.h>
int main(void) {
 int major=0, minor=0, micro=0;
 isoburn_version(&major, &minor, &micro);
 printf("libisoburn native runtime %d.%d.%d\n", major, minor, micro);
 if (major != 1 || minor != 5 || micro != 8) return 1;

 return 0;
}
C
cc $(pkg-config --cflags libisoburn-1) "$fixture/probe.c" -o "$fixture/probe" $(pkg-config --libs libisoburn-1)
"$fixture/probe"
INNER
chroot "$LFS" /usr/bin/env -i PATH=/usr/bin:/usr/sbin LC_ALL=C.UTF-8 \
 PYTHONDONTWRITEBYTECODE=1 /usr/bin/python3 - < /opt/toddy-build/scripts/build/h11/iso-roundtrip.py
