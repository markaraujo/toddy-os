#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
[[ $(dpkg-query --admindir="$LFS/var/lib/dpkg" -W -f='${Status}' gzip) == 'install ok installed' ]]
chroot_run <<'INNER'
set -euo pipefail
printf GZIP_NATIVE_OK > /tmp/toddy-gzip.in
gzip -c /tmp/toddy-gzip.in > /tmp/toddy-gzip.gz
gzip -t /tmp/toddy-gzip.gz
gzip -dc /tmp/toddy-gzip.gz | cmp - /tmp/toddy-gzip.in
rm /tmp/toddy-gzip.{in,gz}
INNER
