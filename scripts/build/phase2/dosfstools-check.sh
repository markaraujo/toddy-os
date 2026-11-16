#!/bin/bash
set -euo pipefail
source /opt/toddy-build/scripts/build/target.sh
guard_target
if [[ $# == 0 ]]; then
    exec unshare --mount --fork bash "$0" --private-dev-proc
fi
[[ $# == 1 && $1 == --private-dev-proc ]]
[[ $(stat -Lc %i /proc/self/ns/mnt) != $(stat -Lc %i /proc/1/ns/mnt) ]]
mount --make-rprivate /
[[ -d /mnt/lfs/dev && ! -L /mnt/lfs/dev && -d /mnt/lfs/proc && ! -L /mnt/lfs/proc ]]
mount --rbind /dev /mnt/lfs/dev
mount -t proc -o nosuid,nodev,noexec proc /mnt/lfs/proc
python3 /opt/toddy-build/scripts/build/phase2/dosfstools_native.py check
