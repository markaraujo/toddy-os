#!/bin/bash
set -euo pipefail
source /opt/toddy-build/scripts/build/h06/common.sh
chroot_run <<'NATIVE'
set -euo pipefail
[[ $(pkg-config --modversion pixman-1) == 0.46.4 ]]
[[ $(dpkg-query -W -f='${Status}' pixman) == 'install ok installed' ]]
test -z "$(dpkg --audit)"
apt-get check
work=$(mktemp -d /tmp/toddy-pixman-consumer.XXXXXX)
trap 'rm -rf "$work"' EXIT
cat > "$work/probe.c" <<'C'
#include <pixman.h>
#include <stdint.h>
#include <string.h>
int main(void) {
    uint32_t source=0xffff0000,destination=0xff0000ff;
    pixman_image_t *src,*dst;
    if (strcmp(pixman_version_string(),"0.46.4")) return 1;
    src=pixman_image_create_bits(PIXMAN_a8r8g8b8,1,1,&source,4);
    dst=pixman_image_create_bits(PIXMAN_a8r8g8b8,1,1,&destination,4);
    if (!src || !dst) return 2;
    pixman_image_composite32(PIXMAN_OP_OVER,src,NULL,dst,0,0,0,0,0,0,1,1);
    if (destination!=0xffff0000) return 3;
    source=0;destination=0xff0000ff;
    pixman_image_composite32(PIXMAN_OP_OVER,src,NULL,dst,0,0,0,0,0,0,1,1);
    if (destination!=0xff0000ff) return 4;
    pixman_image_unref(src);pixman_image_unref(dst);return 0;
}
C
cc "$work/probe.c" $(pkg-config --cflags --libs pixman-1) -o "$work/probe"
"$work/probe"
NATIVE
