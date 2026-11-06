#!/bin/bash
set -euo pipefail
cd /sources/groff-1.24.1
test ! -e /sources/stage/groff
mkdir -p /sources/evidence/h07-groff/initial-missing-path
cp /sources/evidence/h07-groff/check.log test-suite.log src/preproc/eqn/tests/neqn-smoke-test.log /sources/evidence/h07-groff/initial-missing-path/
PATH="$PWD:$PATH" make check 2>&1 | tee /sources/evidence/h07-groff/check.log
make DESTDIR=/sources/stage/groff install
find . -type f \( -name '*.log' -o -name '*.trs' -o -name '*.sum' \) -print0 | tar --null -T - -czf /sources/evidence/h07-groff/test-reports.tar.gz
mkdir -p /sources/stage/groff/usr/share/doc/groff
cat COPYING > /sources/stage/groff/usr/share/doc/groff/copyright
