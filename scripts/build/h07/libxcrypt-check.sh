#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
[[ $(dpkg-query --admindir="$LFS/var/lib/dpkg" -W -f='${Status}' libxcrypt) == 'install ok installed' ]]
chroot_run <<'INNER'
set -euo pipefail
pkg-config --modversion libxcrypt | grep -Fx '4.5.2'
cat > /tmp/toddy-crypt.c <<'C'
#include <crypt.h>
#include <string.h>
int main(void) {
 char *setting = crypt_gensalt("$y$", 0, 0, 0);
 if (!setting) return 1;
 char *hash = crypt("library-smoke-test", setting);
 return !hash || strncmp(hash, "$y$", 3);
}
C
gcc /tmp/toddy-crypt.c -lcrypt -o /tmp/toddy-crypt
/tmp/toddy-crypt
rm /tmp/toddy-crypt{,.c}
INNER
