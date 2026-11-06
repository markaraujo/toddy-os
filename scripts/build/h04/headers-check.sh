#!/bin/bash
source /opt/toddy-build/scripts/build/h04/common.sh
test -f "$LFS/usr/include/linux/version.h"
test -f "$LFS/usr/include/asm/unistd.h"
cat "$LFS/usr/include/linux/version.h"
grep -Fx '#define LINUX_VERSION_CODE 459016' "$LFS/usr/include/linux/version.h"
