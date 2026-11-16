#!/bin/bash
# Fixed builder-to-native entry. Source bind lives only in a private namespace.
set -euo pipefail
[[ $(id -u) == 0 && $# == 1 ]]
case $1 in base|live|qualify-base|qualify-live|finalize-base|finalize-live|stage-live) ;; *) exit 2 ;; esac
source /opt/toddy-build/scripts/build/target.sh
guard_target
exec 9>/var/log/toddy/build/build.lock
flock -n 9
[[ ! -e /var/log/toddy/build/input-sync.running ]]
shopt -s nullglob
running=(/var/log/toddy/build/*.running.json)
[[ ${#running[@]} == 0 ]]
# isolated.sh holds this global lock during compilation; also refuse the
# recognized dispatch/uncertain interval before a terminal job.py receipt.
/usr/bin/python3 -I -c 'import sys;sys.path.insert(0,"/opt/toddy-build/scripts/build/phase2");from image_assemble import unclosed_compiler_jobs;jobs=unclosed_compiler_jobs("/var/log/toddy/phase2");assert not jobs,"Reconcile unclosed compiler jobs: "+repr(jobs)' 
# Require existing native API visibility; never mount another device namespace.
[[ -b /mnt/lfs/dev/vdb4 && -d /mnt/lfs/proc/self && -d /mnt/lfs/sys/dev/block && -d /mnt/lfs/run ]]
exec /usr/bin/unshare --mount --propagation private /usr/bin/bash --noprofile --norc -s -- "$1" <<'NAMESPACE'
set -euo pipefail
[[ $(readlink /proc/self/fd/9) == /var/log/toddy/build/build.lock ]]
flock -n 9
source /opt/toddy-build/scripts/build/target.sh
guard_target
source=/opt/toddy-build
binding=/mnt/lfs/opt/toddy-build
[[ $(readlink -f "$source") == "$source" && $(stat -c '%u:%g' "$source") == 0:0 ]]
mode=$(stat -c %a "$source")
(( (8#$mode & 0022) == 0 ))
[[ -d /mnt/lfs/opt && ! -L /mnt/lfs/opt ]]
# An existing source bind/tree belongs to another operation. Do not unmount it.
[[ ! -e $binding && ! -L $binding ]]
mkdir -m 0755 "$binding"
inode=$(stat -c '%d:%i' "$binding")
mounted=0
cleanup() {
    code=$?
    if (( mounted )); then
        /usr/bin/umount "$binding" || exit 1
    fi
    [[ $(stat -c '%d:%i' "$binding") == "$inode" ]] || exit 1
    rmdir "$binding" || exit 1
    exit "$code"
}
trap cleanup EXIT
/usr/bin/mount --bind "$source" "$binding"
mounted=1
/usr/bin/mount -o remount,bind,ro,nosuid,nodev,noexec "$binding"
options=$(/usr/bin/findmnt -rn -o OPTIONS --mountpoint "$binding")
for flag in ro nosuid nodev noexec; do [[ ,$options, == *,$flag,* ]]; done
[[ $(stat -c '%d:%i' "$source") == $(stat -c '%d:%i' "$binding") ]]
[[ $(readlink /proc/self/ns/mnt) != $(readlink /proc/1/ns/mnt) ]]
# Ubuntu builder uses /usr/sbin/chroot; programs after it are target-native.
/usr/sbin/chroot /mnt/lfs /usr/bin/env -i PATH=/usr/bin:/usr/sbin HOME=/root LC_ALL=C \
    /usr/bin/python3 -I /opt/toddy-build/scripts/build/phase2/image_assemble.py "$1"
NAMESPACE
