#!/bin/bash
set -euo pipefail
cd /sources/gettext-1.0
./configure --disable-shared

make

cp -v gettext-tools/src/{msgfmt,msgmerge,xgettext} /usr/bin
if [[ -f config.log ]]; then cp config.log /sources/evidence/h06-gettext-config.log; fi
