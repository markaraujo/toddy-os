#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
[[ -f /var/log/toddy/build/h07-glibc-install.success.json ]] || exit 1
chroot_run < /opt/toddy-build/scripts/build/h07/glibc-locales-inner.sh
python3 /opt/toddy-build/scripts/build/stage_package.py glibc-locales 2.44-1 \
    "$LFS/sources/stage/glibc-locales" --depends 'glibc (= 2.44-1)' \
    --source glibc-2.44.tar.xz --source glibc-2.44-upstream_fixes-3.patch \
    --recipe /opt/toddy-build/scripts/build/h07/glibc-locales.sh --install
