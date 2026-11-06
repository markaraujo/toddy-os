#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
[[ $(dpkg-query --admindir="$LFS/var/lib/dpkg" -W -f='${Status}' libpipeline) == 'install ok installed' ]]
chroot_run <<'INNER'
set -euo pipefail
cat > /tmp/toddy-pipeline.c <<'C'
#include <pipeline.h>
#include <string.h>
int main(void) { pipeline *p=pipeline_new_command_args("printf","PIPELINE_NATIVE_OK\n",(void*)0); pipeline_want_out(p,-1); pipeline_start(p); const char *line=pipeline_readline(p); int ok=line&&!strcmp(line,"PIPELINE_NATIVE_OK\n"); int status=pipeline_wait(p); pipeline_free(p); return !ok||status; }
C
cc /tmp/toddy-pipeline.c -lpipeline -o /tmp/toddy-pipeline
/tmp/toddy-pipeline
rm /tmp/toddy-pipeline{,.c}
INNER
