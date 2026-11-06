#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
[[ $(dpkg-query --admindir="$LFS/var/lib/dpkg" -W -f='${Status}' pcre2) == 'install ok installed' ]]
chroot_run <<'INNER'
set -euo pipefail
pcre2-config --version | grep -Fx '10.49'
printf 'Toddy caf\303\251\n' | pcre2grep -u 'caf\p{L}' | grep -Fx "$(printf 'Toddy caf\303\251')"
INNER
