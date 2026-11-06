#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
[[ $(dpkg-query --admindir="$LFS/var/lib/dpkg" -W -f='${Status}' ninja) == 'install ok installed' ]]
chroot_run <<'INNER'
set -euo pipefail
ninja --version | grep -Fx '1.13.2'
mkdir /tmp/toddy-ninja-probe
cd /tmp/toddy-ninja-probe
printf 'rule probe\n  command = printf NINJA_OK > $out\nbuild result: probe\n' > build.ninja
ninja -j1
grep -Fx NINJA_OK result
cd /tmp
rm -r toddy-ninja-probe
INNER
