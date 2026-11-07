#!/bin/bash
# Run the shared production recipe against private staging only.
set -euo pipefail
[[ $# == 2 ]]
base=$1
stage=$2
[[ $base == /mnt/lfs/sources/recovery/db-production-* && $(realpath -e "$base") == "$base" ]]
[[ $stage == configure || $stage == build || $stage == install || $stage == postcheck ]]
# Called only inside production-view's private mount namespace.
mount --bind "$base/stage" /mnt/lfs/sources/stage
mount -t tmpfs -o mode=1777,nosuid,nodev tmpfs /mnt/lfs/tmp
mount -t tmpfs -o mode=1777,nosuid,nodev tmpfs /mnt/lfs/var/tmp
virtual=${base#/mnt/lfs}
if [[ $stage == postcheck ]]; then
 chroot /mnt/lfs /usr/bin/env -i HOME=/root TERM=dumb LC_ALL=C \
  PATH=/sources/stage/berkeley-db/usr/bin:/usr/bin:/usr/sbin \
  CPATH=/sources/stage/berkeley-db/usr/include \
  LIBRARY_PATH=/sources/stage/berkeley-db/usr/lib \
  LD_LIBRARY_PATH=/sources/stage/berkeley-db/usr/lib \
  /usr/bin/bash --noprofile --norc -s < "$base/berkeley-db-check-inner.sh"
else
 chroot /mnt/lfs /usr/bin/env -i HOME=/root TERM=dumb LC_ALL=POSIX \
  PATH=/usr/bin:/usr/sbin CONFIG_SITE=/dev/null MAKEFLAGS=-j2 \
  /usr/bin/bash --noprofile --norc -s -- "$stage" < "$base/berkeley-db-production-inner.sh"
fi
