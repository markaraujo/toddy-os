#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
chroot_run <<'INNER'
set -euo pipefail
dpkg-query -S /usr/share/config.site | grep -F lfs-build-support
bash -c 'source /usr/share/config.site; test "$ac_cv_func_posix_spawn_file_actions_addchdir" = yes; test "$ac_cv_func_posix_spawn_file_actions_addfchdir" = yes'
fixture=$(mktemp -d /tmp/lfs-config-site-native.XXXXXX)
trap 'rm -rf "$fixture"' EXIT
cat > "$fixture/probe.c" <<'C'
#define _GNU_SOURCE
#include <spawn.h>
#include <fcntl.h>
#include <unistd.h>
int main(void) {
 posix_spawn_file_actions_t a;
 int fd=open("/tmp",O_RDONLY|O_DIRECTORY);
 if(fd<0 || posix_spawn_file_actions_init(&a)) return 1;
 int result=posix_spawn_file_actions_addchdir(&a,"/tmp") || posix_spawn_file_actions_addfchdir(&a,fd);
 posix_spawn_file_actions_destroy(&a);close(fd);return result;
}
C
cc "$fixture/probe.c" -o "$fixture/probe"
"$fixture/probe"
INNER
