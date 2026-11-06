#!/bin/bash
source /opt/toddy-build/scripts/build/h05/check-common.sh
check_tool file /usr/bin/file 5.48
target_run /usr/bin/file -m "$LFS/usr/share/misc/magic" "$LFS/usr/bin/bash" | grep ELF
