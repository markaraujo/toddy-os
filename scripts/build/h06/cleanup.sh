#!/bin/bash
# LFS 13.1-systemd 7.15; checkpoint disk images only while guest is off.
source /opt/toddy-build/scripts/build/h06/common.sh
chroot_run <<'INNER'
set -euo pipefail
rm -rf /usr/share/{info,man,doc}/*
find /usr/{lib,libexec} -name '*.la' -delete
rm -rf /tools
INNER
