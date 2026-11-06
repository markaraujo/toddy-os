#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
[[ $(dpkg-query --admindir="$LFS/var/lib/dpkg" -W -f='${Status}' libksba) == 'install ok installed' ]]
chroot_run <<'INNER'
set -euo pipefail
cat > /tmp/toddy-ksba.c <<'C'
#include <ksba.h>
int main(void) {ksba_cert_t cert;if(!ksba_check_version("1.8.1") || ksba_cert_new(&cert))return 1;ksba_cert_release(cert);return 0;}
C
cc /tmp/toddy-ksba.c -lksba -o /tmp/toddy-ksba
/tmp/toddy-ksba
rm /tmp/toddy-ksba{,.c}
INNER
