#!/bin/bash
# Frozen LFS 13.1-systemd sections 8.55-8.59; wheel construction stays offline.
set -euo pipefail
cd /sources/wheel-0.48.0
test ! -e /sources/stage/wheel
mkdir -p /sources/evidence/h07-wheel
pip3 wheel -w dist --no-index --no-cache-dir --no-build-isolation --no-deps "$PWD" \
 2>&1 | tee /sources/evidence/h07-wheel/wheel.log
pip3 install --root=/sources/stage/wheel --prefix=/usr --ignore-installed \
 --no-index --no-deps --find-links dist wheel \
 2>&1 | tee /sources/evidence/h07-wheel/install.log
mkdir -p /sources/stage/wheel/usr/share/doc/wheel
cat LICENSE.txt > /sources/stage/wheel/usr/share/doc/wheel/copyright
