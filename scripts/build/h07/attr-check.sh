#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
[[ $(dpkg-query --admindir="$LFS/var/lib/dpkg" -W -f='${Status}' attr) == 'install ok installed' ]]
chroot_run <<'INNER'
set -euo pipefail
getfattr --version | grep -F '2.6.0'
touch /tmp/toddy-xattr
setfattr -n user.toddy -v ATTRIBUTE_OK /tmp/toddy-xattr
getfattr --only-values -n user.toddy /tmp/toddy-xattr | grep -Fx ATTRIBUTE_OK
rm /tmp/toddy-xattr
INNER
