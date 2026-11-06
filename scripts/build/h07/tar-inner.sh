#!/bin/bash
# Frozen LFS 13.1-systemd sections 8.67-8.73; Patch overlay is ADR-0013.
set -euo pipefail
cd /sources/tar-1.35
test ! -e /sources/stage/tar
mkdir -p /sources/evidence/h07-tar
patch --batch --forward --fuzz=0 -Np1 -i ../tar-1.35-acl_fix-1.patch
FORCE_UNSAFE_CONFIGURE=1 ./configure --prefix=/usr
make
# Preserve the raw result; accept only complete source-qualified outcomes.
set +e
make check 2>&1 | tee /sources/evidence/h07-tar/check.log
results=("${PIPESTATUS[@]}")
set -e
[[ ${results[1]} == 0 ]]
printf '%s\n' "${results[0]}" > /sources/evidence/h07-tar/check.exit
if [[ -f tests/testsuite.dir/233/testsuite.log ]]; then
 cp tests/testsuite.dir/233/testsuite.log /sources/evidence/h07-tar/capability-test.log
fi
python3 /sources/toddy-evaluate-tar.py /sources/evidence/h07-tar
make DESTDIR=/sources/stage/tar install
make -C doc DESTDIR=/sources/stage/tar install-html docdir=/usr/share/doc/tar-1.35
find . -type f \( -name '*.log' -o -name '*.trs' -o -name '*.sum' \) -print0 | \
 tar --null -T - -czf /sources/evidence/h07-tar/test-reports.tar.gz
mkdir -p /sources/stage/tar/usr/share/doc/tar
cp COPYING /sources/stage/tar/usr/share/doc/tar/copyright
