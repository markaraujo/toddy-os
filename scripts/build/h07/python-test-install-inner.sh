#!/bin/bash
# Preserve the completed PGO build; repeat all standard tests after DNS setup.
set -euo pipefail
cd /sources/Python-3.14.10
test -x ./python
test -f Makefile
test ! -e /sources/stage/python
mkdir -p /sources/evidence/h07-python/initial-no-resolver
cp /sources/evidence/h07-python/check.log /sources/evidence/h07-python/initial-no-resolver/check.log
make test TESTOPTS="-j8 --timeout 120 --junit-xml=/sources/evidence/h07-python/full-results.xml" 2>&1 | tee /sources/evidence/h07-python/check.log
make DESTDIR=/sources/stage/python install
mkdir -p /sources/stage/python/etc /sources/stage/python/usr/share/doc/python
cat > /sources/stage/python/etc/pip.conf <<'CONF'
[global]
root-user-action = ignore
disable-pip-version-check = true
CONF
cp LICENSE /sources/stage/python/usr/share/doc/python/copyright
# Optional old 3.14.7 HTML docs are not installed as 3.14.10 documentation.
