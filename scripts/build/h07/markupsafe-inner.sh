#!/bin/bash
# Frozen LFS 13.1-systemd sections 8.55-8.59; wheel construction stays offline.
set -euo pipefail
cd /sources/markupsafe-3.0.3
test ! -e /sources/stage/markupsafe
mkdir -p /sources/evidence/h07-markupsafe
pip3 wheel -w dist --no-index --no-cache-dir --no-build-isolation --no-deps "$PWD" \
 2>&1 | tee /sources/evidence/h07-markupsafe/wheel.log
pip3 install --root=/sources/stage/markupsafe --prefix=/usr --ignore-installed \
 --no-index --no-deps --find-links dist markupsafe \
 2>&1 | tee /sources/evidence/h07-markupsafe/install.log
mkdir -p /sources/stage/markupsafe/usr/share/doc/markupsafe
cat LICENSE.txt > /sources/stage/markupsafe/usr/share/doc/markupsafe/copyright
