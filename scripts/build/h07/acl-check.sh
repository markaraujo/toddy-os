#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
[[ $(dpkg-query --admindir="$LFS/var/lib/dpkg" -W -f='${Status}' acl) == 'install ok installed' ]]
chroot_run <<'INNER'
set -euo pipefail
getfacl --version | grep -F '2.4.0'
printf ACL_OK > /tmp/toddy-acl
chmod 600 /tmp/toddy-acl
setfacl -m u:tester:r /tmp/toddy-acl
getfacl -p /tmp/toddy-acl | grep -Fx 'user:tester:r--'
python3 -c 'import os,pwd; user=pwd.getpwnam("tester"); os.setgroups([]); os.setgid(user.pw_gid); os.setuid(user.pw_uid); assert open("/tmp/toddy-acl").read()=="ACL_OK"'
rm /tmp/toddy-acl
INNER
