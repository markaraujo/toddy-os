#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
[[ $(dpkg-query --admindir="$LFS/var/lib/dpkg" -W -f='${Status}' bash) == 'install ok installed' ]]
check_native /usr/bin/bash 5.3
chroot_run <<'INNER'
set -euo pipefail
[[ $(printf '%.3s' native) == nat ]]
trap 'printf TRAP_NATIVE_OK > /tmp/toddy-bash-trap' USR1
kill -USR1 $$
[[ $(cat /tmp/toddy-bash-trap) == TRAP_NATIVE_OK ]]
trap - USR1
rm /tmp/toddy-bash-trap
bash --noprofile --norc -c 'set -euo pipefail; read -r a b < <(printf "6 7\n"); [[ $((a*b)) == 42 ]]; printf BASH_OK'
INNER
