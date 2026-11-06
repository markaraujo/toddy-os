#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
[[ $(dpkg-query --admindir="$LFS/var/lib/dpkg" -W -f='${Status}' bash) == 'install ok installed' ]]
check_native /usr/bin/bash 5.3
chroot_run <<'INNER'
set -euo pipefail
bash --noprofile --norc -c 'set -euo pipefail; read -r a b < <(printf "6 7\n"); [[ $((a*b)) == 42 ]]; printf BASH_OK'
INNER
