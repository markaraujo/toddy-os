#!/bin/bash
source /opt/toddy-build/scripts/build/h05/check-common.sh
check_tool bash /usr/bin/bash 5.3
[[ $(readlink "$LFS/bin/sh") == bash ]]
target_run /usr/bin/bash --noprofile --norc -c 'printf "Target Bash builtin works\n"'
