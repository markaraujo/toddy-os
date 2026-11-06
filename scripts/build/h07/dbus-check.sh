#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
[[ $(dpkg-query --admindir="$LFS/var/lib/dpkg" -W -f='${Status}' dbus) == 'install ok installed' ]]
chroot_run <<'INNER'
set -euo pipefail
dbus-daemon --version | grep -F '1.16.2'
test "$(readlink /var/lib/dbus/machine-id)" = /etc/machine-id
dbus-run-session -- sh -c 'dbus-send --session --print-reply --dest=org.freedesktop.DBus / org.freedesktop.DBus.ListNames' | grep -F org.freedesktop.DBus
INNER
