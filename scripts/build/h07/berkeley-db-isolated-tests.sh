#!/bin/bash
# Test-only canonical-path view of a verified private native build.
set -euo pipefail
source /opt/toddy-build/scripts/build/target.sh
guard_target
[[ $(id -u) == 0 && $# == 2 ]]
fixture=$1
mode=$2
[[ $fixture == /mnt/lfs/sources/recovery/db-standard-* ]]
[[ $(realpath -e -- "$fixture") == "$fixture" ]]
[[ $mode == probe || $mode == standard ]]
for path in "$fixture/source" "$fixture/runtime/tmp" "$fixture/runtime/var-tmp" "$fixture/runtime/shm" /mnt/lfs/tmp /mnt/lfs/var/tmp /mnt/lfs/dev/shm /mnt/lfs/proc; do
 [[ -d $path && ! -L $path ]]
done
exec unshare --mount --ipc --net --pid --fork --kill-child=KILL --mount-proc \
 /bin/bash -s -- "$fixture" "$mode" <<'NAMESPACE'
set -euo pipefail
fixture=$1
mode=$2
mount --make-rprivate /
ip link set lo up
# Preserve compiled wrapper paths while leaving the original mount view intact.
mount --bind "$fixture/source" /mnt/lfs/sources/db-5.3.28
mount --bind "$fixture/runtime/tmp" /mnt/lfs/tmp
mount --bind "$fixture/runtime/var-tmp" /mnt/lfs/var/tmp
mount -t tmpfs -o mode=1777,nosuid,nodev tmpfs "$fixture/runtime/shm"
mount --bind "$fixture/runtime/shm" /mnt/lfs/dev/shm
mount -t proc proc /mnt/lfs/proc
if [[ -d /mnt/lfs/dev/mqueue && ! -L /mnt/lfs/dev/mqueue ]]; then
 mount -t mqueue mqueue /mnt/lfs/dev/mqueue
fi
native_fixture=${fixture#/mnt/lfs}
chroot /mnt/lfs /usr/bin/env -i PATH=/usr/bin:/usr/sbin LC_ALL=C HOME=/root \
 /usr/bin/python3 -B "$native_fixture/isolation-probe.py" "$native_fixture" "$mode"
if [[ $mode == probe ]]; then exit 0;fi
chroot /mnt/lfs /usr/bin/env -i PATH=/usr/bin:/usr/sbin LC_ALL=C HOME=/root \
 /usr/bin/su tester -c 'cd /sources/db-5.3.28/build-test && ./cutest' \
 2>&1 | tee "$fixture/cutest.log"
chroot /mnt/lfs /usr/bin/env -i PATH=/usr/bin:/usr/sbin LC_ALL=C HOME=/root \
 /usr/bin/su tester -c 'cd /sources/db-5.3.28/build-test && /usr/bin/tclsh standard-regression.tcl' \
 2>&1 | tee "$fixture/standard.log"
NAMESPACE
