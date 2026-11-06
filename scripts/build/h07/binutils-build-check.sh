#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
[[ $(cat "$LFS/sources/evidence/h07-binutils/check.exit") == 0 ]]
test -s "$LFS/sources/evidence/h07-binutils/test-reports.tar.gz"
test -x "$LFS/sources/binutils-2.47/build/ld/ld-new"
