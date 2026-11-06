#!/bin/bash
# Frozen LFS 13.1-systemd sections 8.55-8.59; wheel construction stays offline.
set -euo pipefail
cd /sources/setuptools-84.0.0
test ! -e /sources/stage/setuptools
mkdir -p /sources/evidence/h07-setuptools
pip3 wheel -w dist --no-index --no-cache-dir --no-build-isolation --no-deps "$PWD" \
 2>&1 | tee /sources/evidence/h07-setuptools/wheel.log
pip3 install --root=/sources/stage/setuptools --prefix=/usr --ignore-installed \
 --no-index --no-deps --find-links dist setuptools \
 2>&1 | tee /sources/evidence/h07-setuptools/install.log
mkdir -p /sources/stage/setuptools/usr/share/doc/setuptools
cat LICENSE > /sources/stage/setuptools/usr/share/doc/setuptools/copyright
