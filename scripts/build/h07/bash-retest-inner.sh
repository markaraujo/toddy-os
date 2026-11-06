#!/bin/bash
# Repeat the entire unchanged suite with Expect's leaked descriptors closed.
set -euo pipefail
cd /sources/bash-5.3
mkdir -p /sources/evidence/h07-bash/initial
test -s /sources/evidence/h07-bash/initial/check.log
LC_ALL=C.UTF-8 su -s /usr/bin/expect tester <<'EXPECT' 2>&1 | tee /sources/evidence/h07-bash/check.log
set timeout -1
spawn sh -c {exec 3>&- 4>&-; exec make -j1 tests}
expect eof
lassign [wait] _ _ _ value
exit $value
EXPECT
