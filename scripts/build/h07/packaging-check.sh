#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
[[ $(dpkg-query --admindir="$LFS/var/lib/dpkg" -W -f='${Status}' packaging) == 'install ok installed' ]]
chroot_run <<'INNER'
set -euo pipefail
python3 -c 'import packaging; import importlib.metadata as m; assert m.version("packaging")=="26.3"; print("packaging native import OK")'
python3 -c 'from packaging.version import Version; assert Version("1.10") > Version("1.9")'
INNER
