#!/bin/bash
# Frozen LFS 13.1-systemd 8.30; no shared or published login password.
set -euo pipefail
cd /sources/shadow-4.20.2
test ! -e /sources/stage/shadow
find man -name Makefile.in -exec sed -i 's/getspnam\.3 / /' {} \;
find man -name Makefile.in -exec sed -i 's/passwd\.5 / /' {} \;
sed -e 's:#ENCRYPT_METHOD SHA512:ENCRYPT_METHOD YESCRYPT:' \
 -e 's:/var/spool/mail:/var/mail:' \
 -e '/PATH=/{s@/sbin:@@;s@/bin:@@}' -i etc/login.defs
touch /usr/bin/passwd
./configure --sysconfdir=/etc --disable-static --with-{b,yes}crypt \
 --without-libbsd --disable-logind --with-group-name-max-length=32
make
# The frozen book states there is no upstream suite for this package.
make DESTDIR=/sources/stage/shadow exec_prefix=/usr install
make DESTDIR=/sources/stage/shadow -C man install-man
mkdir -p /sources/stage/shadow/usr/share/doc/shadow
cp COPYING /sources/stage/shadow/usr/share/doc/shadow/copyright
