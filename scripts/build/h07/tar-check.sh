#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
[[ $(dpkg-query --admindir="$LFS/var/lib/dpkg" -W -f='${Status}' tar) == 'install ok installed' ]]
chroot_run <<'INNER'
set -euo pipefail
mkdir /tmp/toddy-tar-from /tmp/toddy-tar-to
printf TAR_ACL_OK > /tmp/toddy-tar-from/item
chmod 600 /tmp/toddy-tar-from/item
setfacl -m u:tester:r /tmp/toddy-tar-from/item
tar --acls --xattrs -C /tmp/toddy-tar-from -cf /tmp/toddy-tar.tar item
tar --acls --xattrs -C /tmp/toddy-tar-to -xf /tmp/toddy-tar.tar
getfacl -cp /tmp/toddy-tar-to/item | grep -Fx 'user:tester:r--'
su tester -c 'cat /tmp/toddy-tar-to/item' | grep -Fx TAR_ACL_OK
rm -rf /tmp/toddy-tar-from /tmp/toddy-tar-to /tmp/toddy-tar.tar
INNER
