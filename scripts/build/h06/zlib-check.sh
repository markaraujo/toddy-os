#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
test -f "$LFS/usr/lib/libz.so.1"
test -f "$LFS/usr/include/zlib.h"
