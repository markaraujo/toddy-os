#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
chroot_run <<'INNER'
set -euo pipefail
fixture=$(mktemp -d /tmp/seccomp-native.XXXXXX)
trap 'rm -rf "$fixture"' EXIT
cat > "$fixture/probe.c" <<'C'
#include <seccomp.h>
#include <sys/syscall.h>
#include <unistd.h>
#include <errno.h>
int main(void) {
 scmp_filter_ctx c=seccomp_init(SCMP_ACT_ALLOW);
 if(!c || seccomp_rule_add(c,SCMP_ACT_ERRNO(EPERM),SCMP_SYS(getppid),0) || seccomp_load(c)) return 1;
 errno=0;long r=syscall(SYS_getppid);seccomp_release(c);
 return !(r==-1 && errno==EPERM && getpid()>0);
}
C
cc "$fixture/probe.c" -lseccomp -o "$fixture/probe"
"$fixture/probe"
printf 'Native kernel seccomp denied selected syscall and permitted others\n'
INNER
