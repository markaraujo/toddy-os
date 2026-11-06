#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
[[ $(cat "$LFS/sources/evidence/h07-gcc/check.exit") == 0 ]]
test -s "$LFS/sources/evidence/h07-gcc/test-reports.tar.gz"
test -x "$LFS/sources/gcc-16.2.0/build/gcc/xgcc"
