#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
[[ $(dpkg-query --admindir="$LFS/var/lib/dpkg" -W -f='${Status}' setuptools) == 'install ok installed' ]]
chroot_run <<'INNER'
set -euo pipefail
python3 -c 'import setuptools; import importlib.metadata as m; assert m.version("setuptools")=="84.0.0"; print("setuptools native import OK")'
INNER
