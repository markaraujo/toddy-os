#!/bin/bash
# Frozen BLFS 13.1-systemd recipe with ADR-0017/0021 pinned additions.
set -euo pipefail
cd /sources/curl-8.23.0
test ! -e /sources/stage/curl
mkdir -p /sources/evidence/h07-curl
./configure --prefix=/usr --disable-static --with-openssl \
 --with-ca-path=/etc/ssl/certs --with-ca-bundle=/etc/ssl/certs/ca-certificates.crt \
 --with-nghttp2 --without-libpsl --disable-cookies
make
chown -R tester .
su tester -c 'make -j1 test TFLAGS="-a -j8"' 2>&1 | tee /sources/evidence/h07-curl/check.log
make DESTDIR=/sources/stage/curl install
mkdir -p /sources/stage/curl/usr/share/doc/curl
cat COPYING > /sources/stage/curl/usr/share/doc/curl/copyright
