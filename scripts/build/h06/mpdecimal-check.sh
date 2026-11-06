#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
test -f "$LFS/usr/lib/libmpdec.so"
test -f "$LFS/usr/include/mpdecimal.h"
