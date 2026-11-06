#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
chroot_run <<'INNER'
set -euo pipefail
dpkg-query -S /usr/share/config.site | grep -F lfs-build-support
bash -c 'source /usr/share/config.site; test "$ac_cv_func_posix_spawn_file_actions_addchdir" = yes; test "$ac_cv_func_posix_spawn_file_actions_addfchdir" = yes'
INNER
