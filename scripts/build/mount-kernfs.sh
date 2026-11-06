#!/bin/bash
# LFS 13.1-systemd 7.3: re-enter a saved chroot without recreating accounts.
set -euo pipefail
source /opt/toddy-build/scripts/build/target.sh
guard_target
[[ $(id -u) == 0 ]] || exit 1
mkdir -p "$LFS"/{dev,proc,sys,run}
if ! mountpoint -q "$LFS/dev"; then
    mount --bind /dev "$LFS/dev"
    mount --make-rslave "$LFS/dev"
fi
mountpoint -q "$LFS/dev/pts" || mount -t devpts devpts -o gid=5,mode=0620 "$LFS/dev/pts"
mountpoint -q "$LFS/proc" || mount -t proc proc "$LFS/proc"
mountpoint -q "$LFS/sys" || mount -t sysfs sysfs "$LFS/sys"
mountpoint -q "$LFS/run" || mount -t tmpfs tmpfs "$LFS/run"
if [[ -h $LFS/dev/shm ]]; then
    install -d -m 1777 "$LFS$(realpath /dev/shm)"
else
    mountpoint -q "$LFS/dev/shm" || mount -t tmpfs -o nosuid,nodev tmpfs "$LFS/dev/shm"
fi
findmnt -R "$LFS"

if [[ -L $LFS/etc/resolv.conf && $(readlink "$LFS/etc/resolv.conf") == /run/systemd/resolve/stub-resolv.conf ]]; then
    bash /opt/toddy-build/scripts/build/chroot-resolver.sh
fi
