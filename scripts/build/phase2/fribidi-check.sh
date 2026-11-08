#!/bin/bash
set -euo pipefail
source /opt/toddy-build/scripts/build/h06/common.sh
chroot_run <<'NATIVE'
set -euo pipefail
[[ $(pkg-config --modversion fribidi) == 1.0.16 ]]
[[ $(dpkg-query -W -f='${Status}' fribidi) == 'install ok installed' ]]
test -z "$(dpkg --audit)"
apt-get check
work=$(mktemp -d /tmp/toddy-fribidi-consumer.XXXXXX)
trap 'rm -rf "$work"' EXIT
cat > "$work/probe.c" <<'C'
#include <fribidi.h>
int main(void) {
    FriBidiChar logical[]={0x5d0,0x5d1,0x5d2},visual[3];
    FriBidiStrIndex l2v[3],v2l[3];FriBidiLevel levels[3];FriBidiParType direction=FRIBIDI_PAR_RTL;
    if (!fribidi_log2vis(logical,3,&direction,visual,l2v,v2l,levels)) return 1;
    for (int i=0;i<3;i++) if (visual[i]!=logical[2-i] || l2v[i]!=2-i || v2l[i]!=2-i || !(levels[i]&1)) return 2;
    return 0;
}
C
cc "$work/probe.c" $(pkg-config --cflags --libs fribidi) -o "$work/probe"
"$work/probe"
fribidi --version > "$work/version"
grep -q '1.0.16' "$work/version"
NATIVE
