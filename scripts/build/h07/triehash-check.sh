#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
chroot_run <<'INNER'
set -euo pipefail
fixture=$(mktemp -d /tmp/triehash-native.XXXXXX)
trap 'rm -rf "$fixture"' EXIT
cd "$fixture"
printf 'Alpha = 3\nBeta = 7\n' | triehash --multi-byte=0 -C probe.c -H probe.h
cat > main.c <<'C'
#include "probe.h"
int main(void) {
 return !(PerfectHash("Alpha",5)==3 && PerfectHash("Beta",4)==7 && PerfectHash("absent",6)==Unknown);
}
C
cc probe.c main.c -o probe
./probe
printf 'Native generated perfect hash lookup/rejection passed\n'
INNER
