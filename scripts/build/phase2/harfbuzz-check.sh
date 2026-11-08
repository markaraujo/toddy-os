#!/bin/bash
set -euo pipefail
source /opt/toddy-build/scripts/build/h06/common.sh
chroot_run <<'NATIVE'
set -euo pipefail
[[ $(pkg-config --modversion harfbuzz) == 14.3.1 ]]
[[ $(dpkg-query -W -f='${Status}' harfbuzz) == 'install ok installed' ]]
test -z "$(dpkg --audit)"
apt-get check
work=$(mktemp -d /tmp/toddy-harfbuzz-consumer.XXXXXX)
trap 'rm -rf "$work"' EXIT
cat > "$work/probe.c" <<'C'
#include <hb.h>
#include <hb-ft.h>
#include <string.h>
int main(int argc,char **argv) {
    FT_Library library;FT_Face face;hb_font_t *font;hb_buffer_t *buffer;unsigned int count;
    hb_glyph_info_t *info;hb_glyph_position_t *positions;
    if (argc!=2 || strcmp(hb_version_string(),"14.3.1")) return 1;
    if (FT_Init_FreeType(&library) || FT_New_Face(library,argv[1],0,&face) || FT_Set_Char_Size(face,0,12*64,96,96)) return 2;
    font=hb_ft_font_create_referenced(face);buffer=hb_buffer_create();
    hb_buffer_add_utf8(buffer,"abc",3,0,3);hb_buffer_guess_segment_properties(buffer);
    hb_shape(font,buffer,NULL,0);info=hb_buffer_get_glyph_infos(buffer,&count);
    positions=hb_buffer_get_glyph_positions(buffer,NULL);if (count!=3) return 3;
    for (unsigned i=0;i<count;i++) if (!info[i].codepoint || info[i].cluster!=i || positions[i].x_advance<=0) return 4;
    hb_buffer_destroy(buffer);hb_font_destroy(font);FT_Done_Face(face);FT_Done_FreeType(library);return 0;
}
C
cc "$work/probe.c" $(pkg-config --cflags --libs harfbuzz freetype2) -o "$work/probe"
"$work/probe" /sources/phase2/inputs/harfbuzz-14.3.1/test/api/fonts/Inconsolata-Regular.abc.ttf
PYTHONDONTWRITEBYTECODE=1 python3 - <<'PY'
import gi
gi.require_version('HarfBuzz','0.0')
from gi.repository import HarfBuzz
buffer=HarfBuzz.buffer_create()
assert HarfBuzz.buffer_allocation_successful(buffer)
assert HarfBuzz.buffer_get_length(buffer)==0
PY
NATIVE
