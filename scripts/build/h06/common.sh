#!/bin/bash
# Guest-root wrapper around a clean native target environment.
set -euo pipefail
source /opt/toddy-build/scripts/build/target.sh
guard_target
[[ $(id -u) == 0 ]] || exit 1
SOURCE_TOOL=/opt/toddy-build/scripts/build/source.py
chroot_run() {
    /usr/sbin/chroot "$LFS" /usr/bin/env -i HOME=/root TERM=dumb \
        PATH=/usr/bin:/usr/sbin LC_ALL=POSIX MAKEFLAGS=-j8 TESTSUITEFLAGS=-j8 NINJAJOBS=8 \
        /bin/bash --noprofile --norc -s
}
check_native() {
    local binary=$1 version=$2
    /usr/sbin/chroot "$LFS" /usr/bin/env -i HOME=/root TERM=dumb \
        PATH=/usr/bin:/usr/sbin LC_ALL=POSIX "$binary" --version | grep -F "$version"
}
