#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
cd "$LFS/sources"
python3 "$SOURCE_TOOL" acl-2.4.0.tar.xz
chroot_run < /opt/toddy-build/scripts/build/h07/acl-inner.sh
python3 /opt/toddy-build/scripts/build/h07/evaluate-acl.py
chroot_run <<'INNER'
set -euo pipefail
cd /sources/acl-2.4.0
make DESTDIR=/sources/stage/acl install
mkdir -p /sources/stage/acl/usr/share/doc/acl
cat doc/COPYING doc/COPYING.LGPL > /sources/stage/acl/usr/share/doc/acl/copyright
INNER
python3 /opt/toddy-build/scripts/build/stage_package.py acl 2.4.0-1 \
 "$LFS/sources/stage/acl" --depends 'glibc (>= 2.44-1), attr' --source acl-2.4.0.tar.xz \
 --recipe /opt/toddy-build/scripts/build/h07/acl.sh --install
rm -rf "$LFS/sources/acl-2.4.0"
