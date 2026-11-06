#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
[[ $(dpkg-query --admindir="$LFS/var/lib/dpkg" -W -f='${Status}' gperf) == 'install ok installed' ]]
chroot_run <<'INNER'
set -euo pipefail
printf 'native\npackage\n' | gperf --includes > /tmp/toddy-hash.c
cat >> /tmp/toddy-hash.c <<'C'
int main(void) { return !in_word_set("native",6) || in_word_set("absent",6)!=0; }
C
cc /tmp/toddy-hash.c -o /tmp/toddy-hash
/tmp/toddy-hash
rm /tmp/toddy-hash{,.c}
INNER
