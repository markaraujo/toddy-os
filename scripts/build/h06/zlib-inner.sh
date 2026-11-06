#!/bin/bash
set -euo pipefail
cd /sources/zlib-1.3.2
./configure --prefix=/usr

make

make install

rm -fv /usr/lib/libz.a
if [[ -f config.log ]]; then cp config.log /sources/evidence/h06-zlib-config.log; fi
