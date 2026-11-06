#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
[[ $(dpkg-query --admindir="$LFS/var/lib/dpkg" -W -f='${Status}' diffutils) == 'install ok installed' ]]
chroot_run <<'INNER'
set -euo pipefail
printf 'native\n' > /tmp/toddy-diff-a
cp /tmp/toddy-diff-a /tmp/toddy-diff-b
cmp /tmp/toddy-diff-a /tmp/toddy-diff-b
diff /tmp/toddy-diff-a /tmp/toddy-diff-b
printf 'changed\n' > /tmp/toddy-diff-b
set +e
diff /tmp/toddy-diff-a /tmp/toddy-diff-b
status=$?
set -e
[[ $status == 1 ]]
rm /tmp/toddy-diff-{a,b}
INNER
