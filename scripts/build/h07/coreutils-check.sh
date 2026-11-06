#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
[[ $(dpkg-query --admindir="$LFS/var/lib/dpkg" -W -f='${Status}' coreutils) == 'install ok installed' ]]
chroot_run <<'INNER'
set -euo pipefail
cp --version | grep -F 9.11
printf COREUTILS_ACL_OK > /tmp/toddy-copy-source
chmod 600 /tmp/toddy-copy-source
setfacl -m u:tester:r /tmp/toddy-copy-source
cp --preserve=all /tmp/toddy-copy-source /tmp/toddy-copy-target
getfacl -cp /tmp/toddy-copy-target | grep -Fx 'user:tester:r--'
su tester -c 'cat /tmp/toddy-copy-target' | grep -Fx COREUTILS_ACL_OK
rm /tmp/toddy-copy-{source,target}
printf abc | sha256sum | grep -F ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad
INNER
