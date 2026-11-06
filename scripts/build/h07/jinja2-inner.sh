#!/bin/bash
# Frozen LFS 13.1-systemd sections 8.55-8.59; wheel construction stays offline.
set -euo pipefail
cd /sources/jinja2-3.1.6
test ! -e /sources/stage/jinja2
mkdir -p /sources/evidence/h07-jinja2
pip3 wheel -w dist --no-index --no-cache-dir --no-build-isolation --no-deps "$PWD" \
 2>&1 | tee /sources/evidence/h07-jinja2/wheel.log
pip3 install --root=/sources/stage/jinja2 --prefix=/usr --ignore-installed \
 --no-index --no-deps --find-links dist jinja2 \
 2>&1 | tee /sources/evidence/h07-jinja2/install.log
mkdir -p /sources/stage/jinja2/usr/share/doc/jinja2
cat LICENSE.txt > /sources/stage/jinja2/usr/share/doc/jinja2/copyright
