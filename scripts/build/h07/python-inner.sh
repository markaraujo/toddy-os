#!/bin/bash
# Frozen LFS 13.1-systemd sections 8.52-8.54, explicit Python security overlay.
set -euo pipefail
cd /sources/Python-3.14.10
test ! -e /sources/stage/python
mkdir -p /sources/evidence/h07-python
# Complete five-change series; context-only adaptation verified in ADR-0018.
patch --batch --forward --fuzz=0 -Np1 -i ../Python-3.14.10-openssl_4-1.patch \
 2>&1 | tee /sources/evidence/h07-python/patch.log
./configure --prefix=/usr --enable-shared --with-system-expat --enable-optimizations --without-static-libpython
make
make test TESTOPTS="-j8 --timeout 120" 2>&1 | tee /sources/evidence/h07-python/check.log
make DESTDIR=/sources/stage/python install
mkdir -p /sources/stage/python/etc /sources/stage/python/usr/share/doc/python
cat > /sources/stage/python/etc/pip.conf <<'CONF'
[global]
root-user-action = ignore
disable-pip-version-check = true
CONF
cp LICENSE /sources/stage/python/usr/share/doc/python/copyright
# Optional old 3.14.7 HTML docs are not installed as 3.14.10 documentation.
