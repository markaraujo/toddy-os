#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
[[ $(dpkg-query --admindir="$LFS/var/lib/dpkg" -W -f='${Status}' nghttp2) == 'install ok installed' ]]
chroot_run <<'INNER'
set -euo pipefail
cat > /tmp/toddy-http2.c <<'C'
#include <nghttp2/nghttp2.h>
#include <string.h>
int main(void) { const nghttp2_info *v=nghttp2_version(0); return !v || strcmp(v->version_str,"1.71.0"); }
C
cc /tmp/toddy-http2.c -lnghttp2 -o /tmp/toddy-http2
/tmp/toddy-http2
rm /tmp/toddy-http2{,.c}
INNER
