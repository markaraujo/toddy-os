#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
chroot_run <<'INNER'
set -euo pipefail
[[ $(which bash) == /usr/bin/bash ]]
which --version | grep -F 2.25
INNER
