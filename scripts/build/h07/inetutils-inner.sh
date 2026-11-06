#!/bin/bash
# Frozen LFS 13.1-systemd chapter 8; Expat security overlay per ADR-0013.
set -euo pipefail
cd /sources/inetutils-2.8
test ! -e /sources/stage/inetutils
sed -i 's/def HAVE_TERMCAP_TGETENT/ 1/' telnet/telnet.c
./configure --prefix=/usr --bindir=/usr/bin --localstatedir=/var --disable-logger --disable-whois --disable-rcp --disable-rexec --disable-rlogin --disable-rsh --disable-servers
make
mkdir -p /sources/evidence/h07-inetutils
make check 2>&1 | tee /sources/evidence/h07-inetutils/check.log
find . -type f \( -name '*.log' -o -name '*.trs' \) -print0 | \
 tar --null -T - -czf /sources/evidence/h07-inetutils/test-reports.tar.gz
make DESTDIR=/sources/stage/inetutils install
mkdir -p /sources/stage/inetutils/usr/sbin
mv /sources/stage/inetutils/usr/bin/ifconfig /sources/stage/inetutils/usr/sbin/ifconfig
mkdir -p /sources/stage/inetutils/usr/share/doc/inetutils
cat COPYING > /sources/stage/inetutils/usr/share/doc/inetutils/copyright
