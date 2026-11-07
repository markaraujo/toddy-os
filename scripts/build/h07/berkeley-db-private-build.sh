#!/bin/bash
# Private fresh compilation using the same native recipe as the final build.
set -euo pipefail
source /opt/toddy-build/scripts/build/target.sh
guard_target
[[ $(id -u) == 0 && $# == 2 ]]
base=$1
stage=$2
[[ $base == /mnt/lfs/sources/recovery/db-native-* && $(realpath -e "$base") == "$base" ]]
[[ $stage == prepare || $stage == configure || $stage == build || $stage == helper ]]
for path in "$base/code" "$base/db-5.3.28" "$base/evidence"; do
 [[ -d $path && ! -L $path ]]
done
exec unshare --mount --ipc --net --pid --fork --kill-child=KILL --mount-proc \
 /bin/bash -s -- "$base" "$stage" <<'PRIVATE'
set -euo pipefail
base=$1
stage=$2
mount --make-rprivate /
ip link set lo up
mount --bind "$base/code" /opt/toddy-build
mount --bind "$base/db-5.3.28" /mnt/lfs/sources/db-5.3.28
mount --bind "$base/evidence" /mnt/lfs/sources/evidence/h07-berkeley-db
mount -t tmpfs -o mode=1777,nosuid,nodev tmpfs /mnt/lfs/tmp
mount -t tmpfs -o mode=1777,nosuid,nodev tmpfs /mnt/lfs/var/tmp
mount -t tmpfs -o mode=1777,nosuid,nodev tmpfs /mnt/lfs/dev/shm
mount -t proc proc /mnt/lfs/proc
if [[ $stage == helper ]]; then
 bash /opt/toddy-build/scripts/build/h07/berkeley-db-test-helper.sh
else
 chroot /mnt/lfs /usr/bin/env -i HOME=/root TERM=dumb \
  PATH=/usr/bin:/usr/sbin LC_ALL=POSIX CONFIG_SITE=/dev/null MAKEFLAGS=-j2 \
  /usr/bin/bash --noprofile --norc -s -- "$stage" \
  < /opt/toddy-build/scripts/build/h07/berkeley-db-inner.sh
fi
PRIVATE
