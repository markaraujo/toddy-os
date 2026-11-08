#!/bin/bash
set -euo pipefail
source /opt/toddy-build/scripts/build/h06/common.sh
chroot_run <<'NATIVE'
set -euo pipefail
[[ $(dpkg-query -W -f='${Status}' psutil) == 'install ok installed' ]]
test -z "$(dpkg --audit)"
apt-get check
NATIVE
chroot "$LFS" /usr/bin/env -i PATH=/usr/bin PYTHONDONTWRITEBYTECODE=1 /usr/bin/python3 - < /opt/toddy-build/scripts/build/phase2/psutil-probe.py
