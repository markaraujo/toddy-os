#!/bin/bash
set -euo pipefail
cd /sources/systemd-261.2
[[ -x build/systemd ]]
test ! -e /sources/stage/systemd
cd build
# UTF-8 is required by upstream ellipsis/terminal-width assertions.
set +e
LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8 unshare -m ninja test 2>&1 | tee /sources/evidence/h07-systemd/check.log
results=("${PIPESTATUS[@]}")
set -e
[[ ${results[1]} == 0 ]]
printf '%s\n' "${results[0]}" > /sources/evidence/h07-systemd/check.exit
python3 /sources/toddy-evaluate-systemd.py /sources/evidence/h07-systemd meson-logs/testlog.json
DESTDIR=/sources/stage/systemd ninja install
mkdir -p /sources/stage/systemd/usr/share/man
tar -xf /sources/systemd-man-pages-261.2.tar.xz --no-same-owner --strip-components=1 -C /sources/stage/systemd/usr/share/man
cp -a meson-logs /sources/evidence/h07-systemd/
cd ..
mkdir -p /sources/stage/systemd/usr/share/doc/systemd-261.2
cp -a LICENSES /sources/stage/systemd/usr/share/doc/systemd-261.2/

mkdir -p /sources/stage/systemd/usr/share/doc/systemd
cat LICENSE.GPL2 LICENSE.LGPL2.1 > /sources/stage/systemd/usr/share/doc/systemd/copyright
