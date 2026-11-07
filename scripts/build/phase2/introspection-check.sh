#!/bin/bash
set -euo pipefail
source /opt/toddy-build/scripts/build/h06/common.sh
chroot_run <<'NATIVE'
set -euo pipefail
g-ir-scanner --version | grep -F '1.86.0'
g-ir-compiler --version | grep -F '1.86.0'
[[ $(pkg-config --modversion gobject-introspection-1.0) == 1.86.0 ]]
python3 -c 'from giscanner import _giscanner; assert _giscanner.__file__.startswith("/usr/lib/")'
test -z "$(dpkg --audit)"
apt-get check
NATIVE
