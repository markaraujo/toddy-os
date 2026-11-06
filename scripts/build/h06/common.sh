#!/bin/bash
# Guest-root wrapper around a clean native target environment.
set -euo pipefail
source /opt/toddy-build/scripts/build/target.sh
guard_target
[[ $(id -u) == 0 ]] || exit 1
SOURCE_TOOL=/opt/toddy-build/scripts/build/source.py
chroot_run() {
    local -a native_site=()
    # Patch 49 in the frozen final Glibc overlay removes the aliases assumed
    # by the earlier cross-tool bootstrap cache (ADR-0044).
    if [[ -f /var/log/toddy/build/h07-glibc-install.success.json ]]; then
        native_site=(CONFIG_SITE=/dev/null)
    fi
    /usr/sbin/chroot "$LFS" /usr/bin/env -i HOME=/root TERM=dumb \
        PATH=/usr/bin:/usr/sbin LC_ALL=POSIX MAKEFLAGS=-j8 TESTSUITEFLAGS=-j8 NINJAJOBS=8 \
        "${native_site[@]}" \
        /bin/bash --noprofile --norc -s
}
check_native() {
    local binary=$1 version=$2
    /usr/sbin/chroot "$LFS" /usr/bin/env -i HOME=/root TERM=dumb \
        PATH=/usr/bin:/usr/sbin LC_ALL=POSIX "$binary" --version | grep -F "$version"
}
