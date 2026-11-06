#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
[[ $(dpkg-query --admindir="$LFS/var/lib/dpkg" -W -f='${Status}' groff) == 'install ok installed' ]]
chroot_run <<'INNER'
set -euo pipefail
printf '.TH TODDY 1\n.SH NAME\ntoddy \- native formatter\n' | groff -Tascii -man | grep -F 'native formatter' 
INNER
