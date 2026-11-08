#!/bin/bash
set -euo pipefail
source /opt/toddy-build/scripts/build/h06/common.sh
chroot_run <<'NATIVE'
set -euo pipefail
[[ $(pkg-config --modversion wayland-protocols) == 1.49 ]]
[[ $(dpkg-query -W -f='${Status}' wayland-protocols) == 'install ok installed' ]]
test -z "$(dpkg --audit)"
apt-get check
work=$(mktemp -d /tmp/toddy-protocols-consumer.XXXXXX)
trap 'rm -rf "$work"' EXIT
data=$(pkg-config --variable=pkgdatadir wayland-protocols)
wayland-scanner client-header "$data/stable/xdg-shell/xdg-shell.xml" "$work/xdg-shell-client.h"
wayland-scanner private-code "$data/stable/xdg-shell/xdg-shell.xml" "$work/xdg-shell.c"
cc $(pkg-config --cflags wayland-client) -fPIC -c "$work/xdg-shell.c" -o "$work/xdg-shell.o"
test -s "$work/xdg-shell.o"
NATIVE
