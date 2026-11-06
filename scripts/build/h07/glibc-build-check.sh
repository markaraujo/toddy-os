#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
python3 /opt/toddy-build/scripts/build/h07/evaluate-glibc.py
test -s "$LFS/sources/evidence/h07-glibc/raw-test-results.tar"
test -f "$LFS/sources/glibc-2.44/build/libc.so"
