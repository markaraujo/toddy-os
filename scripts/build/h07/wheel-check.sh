#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
[[ $(dpkg-query --admindir="$LFS/var/lib/dpkg" -W -f='${Status}' wheel) == 'install ok installed' ]]
chroot_run <<'INNER'
set -euo pipefail
python3 -c 'import wheel; import importlib.metadata as m; assert m.version("wheel")=="0.48.0"; print("wheel native import OK")'
INNER
