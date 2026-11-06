#!/bin/bash
# Frozen BLFS 13.1-systemd recipe with authenticated additions in ADR-0026.
set -euo pipefail
cd /sources/gnupg-2.5.24
test ! -e /sources/stage/gnupg
mkdir -p /sources/evidence/h07-gnupg
mkdir build
cd build
../configure --prefix=/usr --localstatedir=/var --sysconfdir=/etc \
 --docdir=/usr/share/doc/gnupg-2.5.24 --disable-ldap --disable-dirmngr \
 --disable-scdaemon --enable-gpgsm --disable-g13 --disable-keyboxd \
 --disable-tpm2d --disable-wks-tools --disable-card-support
make
make check 2>&1 | tee /sources/evidence/h07-gnupg/check.log
make DESTDIR=/sources/stage/gnupg install
cd ..
mkdir -p /sources/stage/gnupg/usr/share/doc/gnupg
cat COPYING* > /sources/stage/gnupg/usr/share/doc/gnupg/copyright
if [[ -d LICENSES ]]; then cp -a LICENSES /sources/stage/gnupg/usr/share/doc/gnupg/; fi
