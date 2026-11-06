#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
[[ -f /var/log/toddy/build/h07-glibc-build.success.json ]] || exit 1
python3 /opt/toddy-build/scripts/build/h07/evaluate-glibc.py
chroot_run < /opt/toddy-build/scripts/build/h07/glibc-install-inner.sh
python3 /opt/toddy-build/scripts/build/stage_package.py glibc 2.44-1 \
    "$LFS/sources/stage/glibc" --source glibc-2.44.tar.xz \
    --source glibc-fhs-1.patch --source glibc-2.44-upstream_fixes-3.patch \
    --conffile /etc/ld.so.conf --conffile /etc/nsswitch.conf --conffile /etc/rpc \
    --recipe /opt/toddy-build/scripts/build/h07/glibc-install.sh --install
chroot_run <<'INNER'
set -euo pipefail
/usr/sbin/ldconfig
INNER
