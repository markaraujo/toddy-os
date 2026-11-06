#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
[[ $(dpkg-query --admindir="$LFS/var/lib/dpkg" -W -f='${Status}' libgpg-error) == 'install ok installed' ]]
chroot_run <<'INNER'
set -euo pipefail
cat > /tmp/toddy-gpg-error.c <<'C'
#include <gpg-error.h>
int main(void) {return !gpg_error_check_version("1.61") || !gpg_strerror(GPG_ERR_EOF);}
C
cc /tmp/toddy-gpg-error.c -lgpg-error -o /tmp/toddy-gpg-error
/tmp/toddy-gpg-error
rm /tmp/toddy-gpg-error{,.c}
INNER
