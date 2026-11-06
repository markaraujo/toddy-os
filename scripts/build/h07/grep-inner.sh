#!/bin/bash
# Frozen LFS 13.1-systemd chapter 8: grep; stage and preserve full tests.
set -euo pipefail
cd /sources/grep-3.12
test ! -e /sources/stage/grep
sed -i "s/echo/#echo/" src/egrep.sh
./configure --prefix=/usr
make
mkdir -p /sources/evidence/h07-grep
make check 2>&1 | tee /sources/evidence/h07-grep/check.log
make DESTDIR=/sources/stage/grep install
mkdir -p /sources/stage/grep/usr/share/doc/grep
cp COPYING /sources/stage/grep/usr/share/doc/grep/copyright
