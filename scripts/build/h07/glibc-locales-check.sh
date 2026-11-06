#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
[[ $(dpkg-query --admindir="$LFS/var/lib/dpkg" -W -f='${Status}' glibc-locales) == 'install ok installed' ]]
chroot_run <<'INNER'
set -euo pipefail
locale -a | grep -Fx en_US.utf8
locale -a | grep -Fx pt_BR.utf8
LC_ALL=pt_BR.UTF-8 locale charmap | grep -Fx UTF-8
INNER
