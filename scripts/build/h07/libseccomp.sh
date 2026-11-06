#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
cd "$LFS/sources"
python3 "$SOURCE_TOOL" libseccomp-2.6.1.tar.gz
chroot_run <<'INNER'
set -euo pipefail
cd /sources/libseccomp-2.6.1
mkdir -p /sources/evidence/h07-libseccomp
./configure --prefix=/usr --disable-static
make
chown -R tester:tester .
su tester -c 'make check' 2>&1 | tee /sources/evidence/h07-libseccomp/check.log
make DESTDIR=/sources/stage/libseccomp install
install -Dm644 LICENSE /sources/stage/libseccomp/usr/share/doc/libseccomp/copyright
INNER
python3 /opt/toddy-build/scripts/build/stage_package.py libseccomp 2.6.1-1 \
 "$LFS/sources/stage/libseccomp" --depends glibc --source libseccomp-2.6.1.tar.gz \
 --recipe /opt/toddy-build/scripts/build/h07/libseccomp.sh --install
