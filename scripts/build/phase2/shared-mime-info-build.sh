#!/bin/bash
set -euo pipefail
[[ $(id -u) == 101 && -d /stage && -d /src/subprojects/xdgmime/src ]]
ulimit -c 0
# Upstream tool regenerates this fixture database; its original XML stays RO.
cp -a /src/tests/mime-db-tests /build/mime-db-tests
meson setup /build/compile /src --prefix=/usr --libdir=lib --buildtype=release \
    --wrap-mode=nofallback -Dbuild-spec=false -Dbuild-tests=true -Dupdate-mimedb=false
ninja -C /build/compile -j4
meson test -C /build/compile --print-errorlogs --num-processes 4
DESTDIR=/stage ninja -C /build/compile install
# Deterministic native generated resources belong to the verified package stage.
/build/compile/src/update-mime-database /stage/usr/share/mime
[[ -f /stage/usr/share/mime/mime.cache && -f /stage/usr/bin/update-mime-database ]]
