#!/bin/bash
# Frozen LFS 13.1-systemd 8.28. DESTDIR maps to upstream FAKEROOT.
set -euo pipefail
cd /sources/libcap-2.78
test ! -e /sources/stage/libcap
sed -i '/install -m.*STA/d' libcap/Makefile
make prefix=/usr lib=lib
mkdir -p /sources/evidence/h07-libcap
make test 2>&1 | tee /sources/evidence/h07-libcap/check.log
make DESTDIR=/sources/stage/libcap prefix=/usr lib=lib install
mkdir -p /sources/stage/libcap/usr/share/doc/libcap
cat License cap/License pam_cap/License psx/License > /sources/stage/libcap/usr/share/doc/libcap/copyright
