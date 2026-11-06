#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
chroot_run <<'INNER'
set -euo pipefail
dpkg-query -S /usr/include/linux/version.h | grep -F linux-api-headers
fixture=$(mktemp -d /tmp/kernel-api-native.XXXXXX)
trap 'rm -rf "$fixture"' EXIT
cat > "$fixture/probe.c" <<'C'
#include <linux/version.h>
#include <linux/openat2.h>
#include <linux/seccomp.h>
_Static_assert(LINUX_VERSION_CODE==KERNEL_VERSION(7,1,8),"Frozen API version mismatch");
int main(void) {struct open_how h={0};return h.flags!=0 || SECCOMP_MODE_FILTER!=2;}
C
cc "$fixture/probe.c" -o "$fixture/probe"
"$fixture/probe"
INNER
