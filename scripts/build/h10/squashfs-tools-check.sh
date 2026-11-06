#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
python3 /opt/toddy-build/scripts/build/h10/require_gate.py
chroot_run <<'INNER'
set -euo pipefail
[[ $(dpkg-query -W -f='${Status} ${Version}' squashfs-tools) == 'install ok installed 4.7.5-1' ]]
dpkg-query -S /usr/bin/mksquashfs /usr/bin/unsquashfs
INNER
# Stream the versioned test into native Python without copying inputs into /usr.
chroot "$LFS" /usr/bin/env -i PATH=/usr/bin:/usr/sbin LC_ALL=C.UTF-8 \
 PYTHONDONTWRITEBYTECODE=1 /usr/bin/python3 - < /opt/toddy-build/scripts/build/h10/squashfs-roundtrip.py
