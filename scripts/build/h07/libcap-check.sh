#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
[[ $(dpkg-query --admindir="$LFS/var/lib/dpkg" -W -f='${Status}' libcap) == 'install ok installed' ]]
chroot_run <<'INNER'
set -euo pipefail
pkg-config --modversion libcap | grep -Fx '2.78'
capsh --print
cp /usr/bin/true /tmp/toddy-capability-probe
setcap cap_net_bind_service=ep /tmp/toddy-capability-probe
getcap /tmp/toddy-capability-probe | grep -F 'cap_net_bind_service=ep'
rm /tmp/toddy-capability-probe
INNER
