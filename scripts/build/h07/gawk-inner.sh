#!/bin/bash
# Frozen LFS 13.1-systemd 8.31; full suite as tester.
set -euo pipefail
cd /sources/gawk-5.4.1
test ! -e /sources/stage/gawk
sed -i 's/extras//' Makefile.in
./configure --prefix=/usr
make
chown -R tester .
mkdir -p /sources/evidence/h07-gawk
su tester -c "PATH=$PATH make check" 2>&1 | tee /sources/evidence/h07-gawk/check.log
make DESTDIR=/sources/stage/gawk install
ln -sv gawk.1 /sources/stage/gawk/usr/share/man/man1/awk.1
install -vDm644 doc/{awkforai.txt,*.{eps,pdf,jpg}} -t /sources/stage/gawk/usr/share/doc/gawk-5.4.1
mkdir -p /sources/stage/gawk/usr/share/doc/gawk
cat COPYING extension/COPYING missing_d/COPYING.LIB > /sources/stage/gawk/usr/share/doc/gawk/copyright
