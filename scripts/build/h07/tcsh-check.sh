#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
chroot_run <<'INNER'
set -euo pipefail
tcsh --version | grep -F 6.24.16
[[ $(readlink /usr/bin/csh) == tcsh ]]
fixture=$(mktemp -d /tmp/csh-native.XXXXXX)
trap 'rm -rf "$fixture"' EXIT
cat > "$fixture/probe.csh" <<'CSH'
set items=(alpha beta)
if ($#items != 2) exit 1
set total=0
foreach item ($items)
 @ total++
end
if ($total != 2) exit 1
/bin/sh -c 'exit 7'
if ($status != 7) exit 1
echo CSH_NATIVE_OK
CSH
/bin/csh -f "$fixture/probe.csh" | grep -Fx CSH_NATIVE_OK
INNER
