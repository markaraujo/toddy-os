#!/bin/bash
set -euo pipefail
cd /sources/bison-3.8.2
./configure --prefix=/usr \
            --docdir=/usr/share/doc/bison-3.8.2

make

make install
if [[ -f config.log ]]; then cp config.log /sources/evidence/h06-bison-config.log; fi
