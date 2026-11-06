#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
cd "$LFS/sources"
python3 "$SOURCE_TOOL" --verify-only glibc-2.44.tar.xz
chroot_run < /opt/toddy-build/scripts/build/h07/glibc-test-locales-inner.sh
python3 /opt/toddy-build/scripts/build/stage_package.py glibc-test-locales 2.44-1 \
 "$LFS/sources/stage/glibc-test-locales" --depends 'glibc (>= 2.44-1), glibc-locales' \
 --source glibc-2.44.tar.xz --recipe /opt/toddy-build/scripts/build/h07/glibc-test-locales.sh --install
