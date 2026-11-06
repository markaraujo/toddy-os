#!/bin/bash
# Frozen LFS 13.1-systemd sections 8.60-8.66; build only in guarded target.
set -euo pipefail
cd /sources/coreutils-9.11
test ! -e /sources/stage/coreutils
mkdir -p /sources/evidence/h07-coreutils
patch --batch --forward --fuzz=0 -Np1 -i ../coreutils-9.11-i18n-1.patch
autoreconf -fv
automake -af
FORCE_UNSAFE_CONFIGURE=1 ./configure --prefix=/usr
make
make NON_ROOT_USERNAME=tester check-root 2>&1 | tee /sources/evidence/h07-coreutils/check-root.log
groupadd -g 102 dummy -U tester
trap 'groupdel dummy' EXIT
chown -R tester .
su tester -c "PATH=$PATH make -k RUN_EXPENSIVE_TESTS=yes check" < /dev/null \
 2>&1 | tee /sources/evidence/h07-coreutils/check.log
groupdel dummy
trap - EXIT
make DESTDIR=/sources/stage/coreutils install
mkdir -p /sources/stage/coreutils/usr/sbin /sources/stage/coreutils/usr/share/man/man8
mv /sources/stage/coreutils/usr/bin/chroot /sources/stage/coreutils/usr/sbin/
mv /sources/stage/coreutils/usr/share/man/man1/chroot.1 /sources/stage/coreutils/usr/share/man/man8/chroot.8
sed -i 's/"1"/"8"/' /sources/stage/coreutils/usr/share/man/man8/chroot.8
find . -type f \( -name '*.log' -o -name '*.trs' -o -name '*.sum' \) -print0 | \
 tar --null -T - -czf /sources/evidence/h07-coreutils/test-reports.tar.gz
mkdir -p /sources/stage/coreutils/usr/share/doc/coreutils
cat COPYING > /sources/stage/coreutils/usr/share/doc/coreutils/copyright
