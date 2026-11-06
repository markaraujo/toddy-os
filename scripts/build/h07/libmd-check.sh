#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
[[ $(dpkg-query --admindir="$LFS/var/lib/dpkg" -W -f='${Status}' libmd) == 'install ok installed' ]]
chroot_run <<'INNER'
set -euo pipefail
cat > /tmp/toddy-md.c <<'C'
#include <md5.h>
#include <string.h>
int main(void) {char out[33]; MD5Data((const unsigned char *)"abc",3,out);return strcmp(out,"900150983cd24fb0d6963f7d28e17f72");}
C
cc /tmp/toddy-md.c -lmd -o /tmp/toddy-md
/tmp/toddy-md
rm /tmp/toddy-md{,.c}
INNER
