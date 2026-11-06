#!/bin/bash
# Staging only after independent full Bash diff-result evaluation.
set -euo pipefail
cd /sources/bash-5.3
test ! -e /sources/stage/bash
make DESTDIR=/sources/stage/bash install
# Each later chroot starts a new /bin/bash; no interactive login reexec.
mkdir -p /sources/stage/bash/usr/share/doc/bash
cp COPYING /sources/stage/bash/usr/share/doc/bash/copyright
