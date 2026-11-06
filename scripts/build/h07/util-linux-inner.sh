#!/bin/bash
# Frozen LFS 13.1-systemd chapter 8; guarded disposable target only.
set -euo pipefail
cd /sources/util-linux-2.42.4
test ! -e /sources/stage/util-linux
mkdir -p /sources/evidence/h07-util-linux
./configure --bindir=/usr/bin --libdir=/usr/lib --runstatedir=/run \
 --sbindir=/usr/sbin --disable-chfn-chsh --disable-login --disable-nologin \
 --disable-su --disable-setpriv --disable-runuser --disable-pylibmount \
 --disable-liblastlog2 --disable-static --without-python \
 ADJTIME_PATH=/var/lib/hwclock/adjtime --docdir=/usr/share/doc/util-linux-2.42.4
make
# Follow the book's unprivileged suite. Never run device tests as root.
touch /etc/fstab
chown -R tester .
su tester -c "make -k check" 2>&1 | tee /sources/evidence/h07-util-linux/check.log
make DESTDIR=/sources/stage/util-linux install

mkdir -p /sources/stage/util-linux/usr/share/doc/util-linux
cat COPYING README.licensing > /sources/stage/util-linux/usr/share/doc/util-linux/copyright
