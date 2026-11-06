#!/bin/bash
# Frozen LFS 13.1-systemd 7.2–7.6; never run outside the guarded build guest.
source /opt/toddy-build/scripts/build/h06/common.sh
for package in m4 ncurses bash coreutils diffutils file findutils gawk grep gzip make patch sed tar xz binutils-pass2 gcc-pass2; do
    [[ -f /var/log/toddy/build/h05-$package.success.json ]] || exit 1
done
chown --from lfs -R root:root "$LFS"/{usr,var,etc,tools,lib64}
mkdir -p "$LFS"/{dev,proc,sys,run}
if ! mountpoint -q "$LFS/dev"; then
    mount --bind /dev "$LFS/dev"
    # Isolate propagation at the guest target boundary.
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
chroot_run < /opt/toddy-build/scripts/build/h06/bootstrap-inner.sh
