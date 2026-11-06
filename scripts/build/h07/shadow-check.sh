#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
[[ $(dpkg-query --admindir="$LFS/var/lib/dpkg" -W -f='${Status}' shadow) == 'install ok installed' ]]
chroot_run <<'INNER'
set -euo pipefail
grep -E '^ENCRYPT_METHOD[[:space:]]+YESCRYPT$' /etc/login.defs
passwd -S root | grep -E '^root L '
useradd -m -s /bin/bash toddy-probe
su -s /bin/bash toddy-probe -c 'test "$(id -un)" = toddy-probe; test -w /home/toddy-probe'
userdel -r toddy-probe
! getent passwd toddy-probe
# The frozen essential account uses /run/dbus as its home. /run is a fresh
# tmpfs after restarting the builder; H08 will provide native tmpfiles setup.
install -d -m755 -o messagebus -g messagebus /run/dbus
pwck -r
grpck -r
INNER
