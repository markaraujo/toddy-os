#!/bin/bash
set -euo pipefail
cd /sources/Python-3.14.7
./configure --prefix=/usr       \
            --enable-shared     \
            --without-ensurepip \
            --without-static-libpython

make

make install
if [[ -f config.log ]]; then cp config.log /sources/evidence/h06-python-config.log; fi
