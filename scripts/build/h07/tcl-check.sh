#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
[[ $(dpkg-query --admindir="$LFS/var/lib/dpkg" -W -f='${Status}' tcl) == 'install ok installed' ]]
chroot_run <<'INNER'
set -euo pipefail
printf 'puts [info patchlevel]\nputs [expr {6*7}]\n' | tclsh > /tmp/toddy-tcl-result
grep -Fx '8.6.18' /tmp/toddy-tcl-result
grep -Fx '42' /tmp/toddy-tcl-result
rm /tmp/toddy-tcl-result
INNER
