#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
[[ $(dpkg-query --admindir="$LFS/var/lib/dpkg" -W -f='${Status}' texinfo) == 'install ok installed' ]]
chroot_run <<'INNER'
set -euo pipefail
printf '\input texinfo\n@setfilename native.info\n@node Top\n@top Native\nTEXINFO_NATIVE_OK\n@bye\n' > /tmp/toddy-native.texi
makeinfo -o /tmp/toddy-native.info /tmp/toddy-native.texi
grep -F TEXINFO_NATIVE_OK /tmp/toddy-native.info
rm /tmp/toddy-native.{texi,info}
INNER
