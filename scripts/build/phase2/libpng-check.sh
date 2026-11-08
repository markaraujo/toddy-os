#!/bin/bash
set -euo pipefail
source /opt/toddy-build/scripts/build/h06/common.sh
chroot_run <<'NATIVE'
set -euo pipefail
[[ $(pkg-config --modversion libpng) == 1.6.58 ]]
[[ $(dpkg-query -W -f='${Status}' libpng) == 'install ok installed' ]]
test -z "$(dpkg --audit)"
apt-get check
work=$(mktemp -d /tmp/toddy-png-consumer.XXXXXX)
trap 'rm -rf "$work"' EXIT
cat > "$work/probe.c" <<'C'
#include <png.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
int main(void) {
    png_image image; png_alloc_size_t size=0; void *encoded; uint8_t input[4]={255,0,0,255},output[4]={0};
    if (strcmp(png_get_libpng_ver(NULL),"1.6.58")) return 1;
    memset(&image,0,sizeof(image));image.version=PNG_IMAGE_VERSION;
    image.width=1;image.height=1;image.format=PNG_FORMAT_RGBA;
    if (!png_image_write_to_memory(&image,NULL,&size,0,input,0,NULL) || !size) return 2;
    encoded=malloc(size);if (!encoded) return 3;
    if (!png_image_write_to_memory(&image,encoded,&size,0,input,0,NULL)) return 4;
    png_image_free(&image);memset(&image,0,sizeof(image));image.version=PNG_IMAGE_VERSION;
    if (!png_image_begin_read_from_memory(&image,encoded,size)) return 5;
    image.format=PNG_FORMAT_RGBA;
    if (image.width!=1 || image.height!=1 || !png_image_finish_read(&image,NULL,output,0,NULL)) return 6;
    if (memcmp(input,output,4)) return 7;
    png_image_free(&image);free(encoded);return 0;
}
C
cc "$work/probe.c" $(pkg-config --cflags --libs libpng) -o "$work/probe"
"$work/probe"
NATIVE
