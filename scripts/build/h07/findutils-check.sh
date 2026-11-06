#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
[[ $(dpkg-query --admindir="$LFS/var/lib/dpkg" -W -f='${Status}' findutils) == 'install ok installed' ]]
chroot_run <<'INNER'
set -euo pipefail
mkdir /tmp/toddy-find
printf native > /tmp/toddy-find/item
[[ $(find /tmp/toddy-find -type f -print) == /tmp/toddy-find/item ]]
find /tmp/toddy-find -type f -print0 | xargs -0 cat | grep -Fx native
rm -r /tmp/toddy-find
python3 - <<'CHECK'
import os,subprocess,tempfile
base=tempfile.mkdtemp(prefix='/tmp/toddy-find-greek-')
name=os.fsencode(base)+b'/\xf2'
try:
 fd=os.open(name,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600);os.close(fd)
 env=dict(os.environ,LC_ALL='el_GR.iso88597')
 output=subprocess.check_output([b'/usr/bin/find',os.fsencode(base),b'-regextype',b'posix-extended',b'-type',b'f',b'-iregex',b'.*/\xd3',b'-print0'],env=env)
 assert output==name+b'\0',repr(output)
 print('Native Greek sigma case-insensitive regex passed')
finally:
 os.unlink(name);os.rmdir(base)
CHECK
INNER
