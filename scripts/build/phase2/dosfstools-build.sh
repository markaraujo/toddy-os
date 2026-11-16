#!/bin/bash
# BLFS13.1-systemd dosfstools4.2, UID101 qualified read-only-input harness only.
set -euo pipefail
[[ $(id -u) == 101 && -f /src/configure && ! -e /build/compile ]]
[[ -z $(find /stage -mindepth 1 -print -quit) ]]
command -v xxd > /build/xxd-path.txt
xxd -v > /build/xxd-version.txt 2>&1
# Keep the complete upstream in-tree test fixture layout in writable build data;
# source mount stays read-only. test-fsck reads local .args files, not VPATH.
cp -R --no-preserve=ownership /src /build/compile
cd /build/compile
./configure --prefix=/usr --sbindir=/usr/sbin --enable-compat-symlinks \
    --mandir=/usr/share/man --docdir=/usr/share/doc/dosfstools-4.2
make -j4
# Never accept configure's optional xxd fallback (which skips every test).
grep -Fx 'XXD_FOUND = yes' tests/Makefile
make -j1 check > /build/original-tests.log 2>&1
printf '0\n' > /build/original-tests.exit
make DESTDIR=/stage install
python3 /src/toddy-inspect.py tests /build/compile/tests /src/tests/Makefile.am > /build/original-tests.json
python3 /src/toddy-file-probe.py --directory /build --tools /stage/usr/sbin > /build/fat32-file-probe.json
python3 /src/verify_stage.py /stage > /build/stage-results.json
