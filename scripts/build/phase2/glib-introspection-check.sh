#!/bin/bash
set -euo pipefail
source /opt/toddy-build/scripts/build/h06/common.sh
chroot_run <<'NATIVE'
set -euo pipefail
for namespace in GLib-2.0 GObject-2.0 Gio-2.0 GIRepository-3.0; do
    test -s "/usr/lib/girepository-1.0/$namespace.typelib"
    test -s "/usr/share/gir-1.0/$namespace.gir"
done
gi-inspect-typelib --print-shlibs --print-typelibs Gio
gi-inspect-typelib --print-shlibs --print-typelibs GIRepository
[[ $(pkg-config --modversion girepository-2.0) == 2.88.3 ]]
test -z "$(dpkg --audit)"
apt-get check
NATIVE
