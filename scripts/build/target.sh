#!/bin/bash
# Source only in the dedicated disposable VM.
set -euo pipefail
export LFS=/mnt/lfs
TARGET_DISK=/dev/vdb
TARGET_ROOT=/dev/vdb4

guard_guest() {
    [[ $(hostname) == toddy-builder ]] || { echo 'Wrong guest hostname' >&2; return 1; }
    [[ $(systemd-detect-virt) == kvm || $(systemd-detect-virt) == qemu ]] || return 1
    [[ $(lsblk -dn -o SERIAL "$TARGET_DISK") == TODDY-LFS-TARGET ]] || return 1
    [[ $(blockdev --getsize64 "$TARGET_DISK") == 193273528320 ]] || return 1
    [[ $(lsblk -dn -o SERIAL /dev/vda) == TODDY-BUILDER ]] || return 1
    [[ $(findmnt -n -o SOURCE /) == /dev/vda1 ]] || return 1
    [[ $LFS == /mnt/lfs && ! -L $LFS ]] || return 1
}

guard_target() {
    guard_guest
    [[ $(findmnt -n -o SOURCE --mountpoint "$LFS") == "$TARGET_ROOT" ]] || return 1
    [[ $(findmnt -n -o FSTYPE --mountpoint "$LFS") == ext4 ]] || return 1
    [[ $(blkid -s LABEL -o value "$TARGET_ROOT") == TODDY_LFS ]] || return 1
    [[ $(lsblk -dn -o PKNAME "$TARGET_ROOT") == vdb ]] || return 1
    [[ $(stat -c %a "$LFS") == 755 ]] || return 1
    [[ $(df --output=avail -k "$LFS" | tail -1) -gt 10485760 ]] || return 1
    [[ ! -e $LFS/usr/lib64 ]] || return 1
}
