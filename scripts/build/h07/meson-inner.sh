#!/bin/bash
# Frozen LFS 13.1-systemd sections 8.55-8.59; wheel construction stays offline.
set -euo pipefail
cd /sources/meson-1.12.0
test ! -e /sources/stage/meson
mkdir -p /sources/evidence/h07-meson
pip3 wheel -w dist --no-index --no-cache-dir --no-build-isolation --no-deps "$PWD" \
 2>&1 | tee /sources/evidence/h07-meson/wheel.log
pip3 install --root=/sources/stage/meson --prefix=/usr --ignore-installed \
 --no-index --no-deps --find-links dist meson \
 2>&1 | tee /sources/evidence/h07-meson/install.log
mkdir -p /sources/stage/meson/usr/share/doc/meson
cat COPYING > /sources/stage/meson/usr/share/doc/meson/copyright
