#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
[[ $(dpkg-query --admindir="$LFS/var/lib/dpkg" -W -f='${Status}' markupsafe) == 'install ok installed' ]]
chroot_run <<'INNER'
set -euo pipefail
python3 -c "from markupsafe import escape, _speedups; assert _speedups.__file__.endswith('.so'); assert str(escape('<native>'))=='&lt;native&gt;'"
INNER
