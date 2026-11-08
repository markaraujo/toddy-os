#!/bin/bash
set -euo pipefail
source /opt/toddy-build/scripts/build/h06/common.sh
chroot_run <<'NATIVE'
set -euo pipefail
[[ $(pkg-config --modversion cairo cairo-gobject cairo-ft) == $'1.18.4\n1.18.4\n1.18.4' ]]
[[ $(dpkg-query -W -f='${Status}' cairo) == 'install ok installed' ]]
test -z "$(dpkg --audit)"
apt-get check
work=$(mktemp -d /tmp/toddy-cairo-consumer.XXXXXX)
trap 'rm -rf "$work"' EXIT
cat > "$work/probe.c" <<'C'
#include <cairo.h>
#include <cairo-gobject.h>
#include <fontconfig/fontconfig.h>
#include <stdint.h>
#include <string.h>
int main(int argc,char **argv) {
    cairo_surface_t *surface,*decoded;cairo_t *cr;uint32_t *pixels;int stride,changed=0;
    cairo_text_extents_t extents;
    if (argc!=3 || strcmp(cairo_version_string(),"1.18.4") || !cairo_gobject_surface_get_type()) return 1;
    if (!FcConfigAppFontAddFile(NULL,(const FcChar8*)argv[1])) return 2;
    surface=cairo_image_surface_create(CAIRO_FORMAT_ARGB32,128,48);cr=cairo_create(surface);
    cairo_set_source_rgb(cr,1,0,0);cairo_paint(cr);cairo_surface_flush(surface);
    pixels=(uint32_t*)cairo_image_surface_get_data(surface);if (pixels[0]!=0xffff0000u) return 3;
    cairo_select_font_face(cr,"Inconsolata",CAIRO_FONT_SLANT_NORMAL,CAIRO_FONT_WEIGHT_NORMAL);
    cairo_set_font_size(cr,24);cairo_text_extents(cr,"abc",&extents);
    if (extents.width<=0 || extents.x_advance<=0) return 4;
    cairo_set_source_rgb(cr,1,1,1);cairo_move_to(cr,8,32);cairo_show_text(cr,"abc");
    if (cairo_status(cr)!=CAIRO_STATUS_SUCCESS) return 5;
    cairo_surface_flush(surface);stride=cairo_image_surface_get_stride(surface)/4;
    for (int y=0;y<48;y++) for (int x=0;x<128;x++) if (pixels[y*stride+x]!=0xffff0000u) changed++;
    if (changed<10 || cairo_surface_write_to_png(surface,argv[2])!=CAIRO_STATUS_SUCCESS) return 6;
    decoded=cairo_image_surface_create_from_png(argv[2]);
    if (cairo_surface_status(decoded)!=CAIRO_STATUS_SUCCESS || cairo_image_surface_get_width(decoded)!=128 || cairo_image_surface_get_height(decoded)!=48) return 7;
    cairo_surface_flush(decoded);
    if (cairo_image_surface_get_stride(decoded)!=stride*4) return 8;
    uint32_t *readback=(uint32_t*)cairo_image_surface_get_data(decoded);
    for (int i=0;i<stride*48;i++) if ((pixels[i]&0xffffffu)!=(readback[i]&0xffffffu)) return 9;
    cairo_surface_destroy(decoded);cairo_destroy(cr);cairo_surface_destroy(surface);return 0;
}
C
cc "$work/probe.c" $(pkg-config --cflags --libs cairo cairo-gobject fontconfig) -o "$work/probe"
"$work/probe" /sources/phase2/inputs/harfbuzz-14.3.1/test/api/fonts/Inconsolata-Regular.abc.ttf "$work/image.png"
NATIVE
