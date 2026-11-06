#!/bin/bash
# Frozen LFS 13.1-systemd sections 8.55-8.59; wheel construction stays offline.
set -euo pipefail
cd /sources/packaging-26.3
test ! -e /sources/stage/packaging
mkdir -p /sources/evidence/h07-packaging
pip3 wheel -w dist --no-index --no-cache-dir --no-build-isolation --no-deps "$PWD" \
 2>&1 | tee /sources/evidence/h07-packaging/wheel.log
pip3 install --root=/sources/stage/packaging --prefix=/usr --ignore-installed \
 --no-index --no-deps --find-links dist packaging \
 2>&1 | tee /sources/evidence/h07-packaging/install.log
mkdir -p /sources/stage/packaging/usr/share/doc/packaging
cat LICENSE LICENSE.APACHE LICENSE.BSD > /sources/stage/packaging/usr/share/doc/packaging/copyright
