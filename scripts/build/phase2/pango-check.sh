#!/bin/bash
set -euo pipefail
source /opt/toddy-build/scripts/build/h06/common.sh
chroot_run <<'NATIVE'
set -euo pipefail
[[ $(pkg-config --modversion pango pangocairo) == $'1.58.2\n1.58.2' ]]
[[ $(dpkg-query -W -f='${Status}' pango) == 'install ok installed' ]]
test -z "$(dpkg --audit)"
apt-get check
work=$(mktemp -d /tmp/toddy-pango-consumer.XXXXXX)
trap 'rm -rf "$work"' EXIT
cat > "$work/probe.c" <<'C'
#include <pango/pangocairo.h>
#include <stdint.h>
#include <string.h>
int main(int argc,char **argv) {
    PangoFontMap *map;PangoContext *context;PangoLayout *layout;
    PangoFontDescription *description;GError *error=NULL;cairo_surface_t *surface;cairo_t *cr;
    int width,height,changed=0,stride;uint32_t *pixels;
    if (argc!=2 || strcmp(pango_version_string(),"1.58.2")) return 1;
    map=pango_cairo_font_map_new();
    if (!pango_font_map_add_font_file(map,argv[1],&error) || error) return 2;
    context=pango_font_map_create_context(map);layout=pango_layout_new(context);
    description=pango_font_description_from_string("Cantarell 12");
    pango_layout_set_font_description(layout,description);pango_layout_set_width(layout,100*PANGO_SCALE);
    pango_layout_set_wrap(layout,PANGO_WRAP_WORD_CHAR);
    pango_layout_set_text(layout,"Olá, Toddy OS — texto legível offline.",-1);
    pango_layout_get_pixel_size(layout,&width,&height);
    if (pango_layout_get_line_count(layout)<2 || width<=0 || height<=0 || width>100) return 3;
    surface=cairo_image_surface_create(CAIRO_FORMAT_ARGB32,128,128);cr=cairo_create(surface);
    cairo_set_source_rgb(cr,0,0,0);cairo_paint(cr);cairo_set_source_rgb(cr,1,1,1);
    pango_cairo_update_layout(cr,layout);pango_cairo_show_layout(cr,layout);cairo_surface_flush(surface);
    if (cairo_status(cr)!=CAIRO_STATUS_SUCCESS) return 4;
    pixels=(uint32_t*)cairo_image_surface_get_data(surface);stride=cairo_image_surface_get_stride(surface)/4;
    for (int y=0;y<128;y++) for (int x=0;x<128;x++) if ((pixels[y*stride+x]&0xffffffu)!=0) changed++;
    if (changed<10) return 5;
    if (pango_parse_markup("<b>unclosed",-1,0,NULL,NULL,NULL,&error) || !error) return 6;
    g_clear_error(&error);cairo_destroy(cr);cairo_surface_destroy(surface);
    pango_font_description_free(description);g_object_unref(layout);g_object_unref(context);g_object_unref(map);
    return 0;
}
C
cc "$work/probe.c" $(pkg-config --cflags --libs pangocairo) -o "$work/probe"
"$work/probe" /sources/phase2/inputs/pango-1.58.2/tests/fonts/Cantarell-VF.otf
PYTHONDONTWRITEBYTECODE=1 python3 - <<'PY'
import gi
gi.require_version('Pango','1.0');gi.require_version('PangoCairo','1.0')
from gi.repository import Pango,PangoCairo
description=Pango.FontDescription.from_string('Cantarell 12')
assert description.get_family()=='Cantarell'
assert description.get_size()==12*Pango.SCALE
PY
NATIVE
