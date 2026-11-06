#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
[[ $(dpkg-query --admindir="$LFS/var/lib/dpkg" -W -f='${Status}' flit-core) == 'install ok installed' ]]
chroot_run <<'INNER'
set -euo pipefail
python3 -c 'import flit_core; import importlib.metadata as m; assert m.version("flit_core")=="4.0.2"; print("flit-core native import OK")'
INNER
