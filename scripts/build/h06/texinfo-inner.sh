#!/bin/bash
set -euo pipefail
cd /sources/texinfo-7.3
./configure --prefix=/usr

make

make install
if [[ -f config.log ]]; then cp config.log /sources/evidence/h06-texinfo-config.log; fi
