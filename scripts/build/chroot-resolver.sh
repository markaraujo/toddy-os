#!/bin/bash
# Build-only resolver data on the target's separate /run tmpfs, never image data.
set -euo pipefail
source /opt/toddy-build/scripts/build/target.sh
guard_target
[[ $(id -u) == 0 ]]
[[ $(readlink "$LFS/etc/resolv.conf") == /run/systemd/resolve/stub-resolv.conf ]]
[[ $(findmnt -n -o FSTYPE --mountpoint "$LFS/run") == tmpfs ]]
source_resolver=$(readlink -f /etc/resolv.conf)
[[ -f $source_resolver ]]
install -dm755 "$LFS/run/systemd/resolve"
[[ ! -L $LFS/run/systemd/resolve/stub-resolv.conf ]]
install -m644 "$source_resolver" "$LFS/run/systemd/resolve/stub-resolv.conf"
printf 'Prepared build-only resolver on separate target runtime tmpfs\n'
