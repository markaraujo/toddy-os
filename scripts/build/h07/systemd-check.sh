#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
[[ $(dpkg-query --admindir="$LFS/var/lib/dpkg" -W -f='${Status}' systemd) == 'install ok installed' ]]
chroot_run <<'INNER'
set -euo pipefail
systemctl --version | grep -F 'systemd 261'
udevadm --version | grep -F 261
test -x /usr/lib/systemd/systemd
test -s /etc/machine-id
[[ $(readlink /usr/sbin/init) == ../lib/systemd/systemd || $(readlink /usr/bin/init) == ../lib/systemd/systemd ]]
systemd-escape --path '/toddy native/check' | grep -F 'toddy\x20native-check'
INNER
