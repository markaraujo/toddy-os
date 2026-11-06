#!/bin/bash
set -euo pipefail
cd /sources/mpdecimal-4.0.1
./configure --prefix=/usr    \
            --disable-static \
            --docdir=/usr/share/doc/mpdecimal-4.0.1

make

make install
if [[ -f config.log ]]; then cp config.log /sources/evidence/h06-mpdecimal-config.log; fi
