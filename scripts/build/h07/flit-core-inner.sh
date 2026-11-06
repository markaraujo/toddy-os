#!/bin/bash
# Frozen LFS 13.1-systemd sections 8.55-8.59; wheel construction stays offline.
set -euo pipefail
cd /sources/flit_core-4.0.2
test ! -e /sources/stage/flit-core
mkdir -p /sources/evidence/h07-flit-core
pip3 wheel -w dist --no-index --no-cache-dir --no-build-isolation --no-deps "$PWD" \
 2>&1 | tee /sources/evidence/h07-flit-core/wheel.log
pip3 install --root=/sources/stage/flit-core --prefix=/usr --ignore-installed \
 --no-index --no-deps --find-links dist flit_core \
 2>&1 | tee /sources/evidence/h07-flit-core/install.log
mkdir -p /sources/stage/flit-core/usr/share/doc/flit-core
cat LICENSE > /sources/stage/flit-core/usr/share/doc/flit-core/copyright
