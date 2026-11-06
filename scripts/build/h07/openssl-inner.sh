#!/bin/bash
# Frozen LFS 13.1-systemd chapter 8; security overlays and generic ISA explicit.
set -euo pipefail
cd /sources/openssl-4.0.3
test ! -e /sources/stage/openssl
./config --prefix=/usr --openssldir=/etc/ssl --libdir=lib shared zlib-dynamic
make
mkdir -p /sources/evidence/h07-openssl
HARNESS_JOBS=8 make test 2>&1 | tee /sources/evidence/h07-openssl/check.log
find . -type f \( -name '*.log' -o -name '*.trs' -o -name '*.sum' \) -print0 | \
 tar --null -T - -czf /sources/evidence/h07-openssl/test-reports.tar.gz
make DESTDIR=/sources/stage/openssl INSTALL_LIBS= MANSUFFIX=ssl install
mv /sources/stage/openssl/usr/share/doc/openssl /sources/stage/openssl/usr/share/doc/openssl-4.0.3
cp -vfr doc/* /sources/stage/openssl/usr/share/doc/openssl-4.0.3
mkdir -p /sources/stage/openssl/usr/share/doc/openssl
cat LICENSE.txt > /sources/stage/openssl/usr/share/doc/openssl/copyright
