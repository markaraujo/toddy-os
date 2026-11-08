#!/bin/bash
set -euo pipefail
source /opt/toddy-build/scripts/build/h06/common.sh
chroot_run <<'NATIVE'
set -euo pipefail
[[ $(pkg-config --modversion libjpeg libturbojpeg) == $'3.2.0\n3.2.0' ]]
[[ $(dpkg-query -W -f='${Status}' libjpeg-turbo) == 'install ok installed' ]]
test -z "$(dpkg --audit)"
apt-get check
work=$(mktemp -d /tmp/toddy-jpeg-consumer.XXXXXX)
trap 'rm -rf "$work"' EXIT
cat > "$work/probe.c" <<'C'
#include <stdio.h>
#include <stdlib.h>
#include <jpeglib.h>
int main(void) {
    struct jpeg_compress_struct c;struct jpeg_decompress_struct d;
    struct jpeg_error_mgr ce,de;unsigned char *data=NULL;unsigned long size=0;
    unsigned char row[24],decoded[24];JSAMPROW rows[]={row},out[]={decoded};
    c.err=jpeg_std_error(&ce);jpeg_create_compress(&c);jpeg_mem_dest(&c,&data,&size);
    c.image_width=8;c.image_height=8;c.input_components=3;c.in_color_space=JCS_RGB;
    jpeg_set_defaults(&c);jpeg_set_quality(&c,100,TRUE);jpeg_start_compress(&c,TRUE);
    for(int i=0;i<24;i++)row[i]=i%3==0?240:16;
    while(c.next_scanline<c.image_height)if(jpeg_write_scanlines(&c,rows,1)!=1)return 1;
    jpeg_finish_compress(&c);jpeg_destroy_compress(&c);
    if(size<4 || data[0]!=255 || data[1]!=216)return 2;
    d.err=jpeg_std_error(&de);jpeg_create_decompress(&d);jpeg_mem_src(&d,data,size);
    if(jpeg_read_header(&d,TRUE)!=JPEG_HEADER_OK)return 3;
    d.out_color_space=JCS_RGB;jpeg_start_decompress(&d);
    if(d.output_width!=8 || d.output_height!=8 || d.output_components!=3)return 4;
    while(d.output_scanline<d.output_height) {
        if(jpeg_read_scanlines(&d,out,1)!=1)return 5;
        for(int i=0;i<24;i++)if(abs((int)decoded[i]-(int)row[i])>3)return 6;
    }
    jpeg_finish_decompress(&d);jpeg_destroy_decompress(&d);free(data);return 0;
}
C
cc "$work/probe.c" -ljpeg -o "$work/probe"
"$work/probe"
NATIVE
