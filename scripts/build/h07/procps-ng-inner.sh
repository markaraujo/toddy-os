#!/bin/bash
# Frozen LFS 13.1-systemd chapter 8; guarded disposable target only.
set -euo pipefail
cd /sources/procps-ng-4.0.7
test ! -e /sources/stage/procps-ng
mkdir -p /sources/evidence/h07-procps-ng
./configure --prefix=/usr --docdir=/usr/share/doc/procps-ng-4.0.7 \
 --disable-static --disable-kill --enable-watch8bit --with-systemd
make
chown -R tester .
su tester -c "PATH=$PATH make check" 2>&1 | tee /sources/evidence/h07-procps-ng/check.log
make DESTDIR=/sources/stage/procps-ng install

mkdir -p /sources/stage/procps-ng/usr/share/doc/procps-ng
cat COPYING COPYING.LIB > /sources/stage/procps-ng/usr/share/doc/procps-ng/copyright
