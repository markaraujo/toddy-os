#!/bin/bash
# Frozen LFS 13.1-systemd 8.27: retain known temporary-Coreutils exception.
set -euo pipefail
cd /sources/acl-2.4.0
test ! -e /sources/stage/acl
./configure --prefix=/usr --disable-static --docdir=/usr/share/doc/acl-2.4.0
make
mkdir -p /sources/evidence/h07-acl
set +e
make check > /sources/evidence/h07-acl/check.log 2>&1
result=$?
set -e
printf '%s\n' "$result" > /sources/evidence/h07-acl/check.exit
find . -type f \( -name '*.log' -o -name '*.trs' \) -print0 | \
 tar --null -T - -czf /sources/evidence/h07-acl/test-reports.tar.gz
cat /sources/evidence/h07-acl/check.log
# The outer strict evaluator accepts only the book's exact cp.run failure.
