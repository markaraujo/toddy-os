#!/bin/bash
set -euo pipefail
source /opt/toddy-build/scripts/build/h06/common.sh
chroot_run <<'NATIVE'
set -euo pipefail
[[ $(dpkg-query -W -f='${Status}' dejavu-fonts) == 'install ok installed' ]]
test -z "$(dpkg --audit)"
apt-get check
python3 - <<'PY'
import subprocess
from pathlib import Path
fonts=list(Path('/usr/share/fonts/dejavu').glob('*.ttf'));assert len(fonts)==4
expected={'DejaVuSerif.ttf':(80,0),'DejaVuSerif-Bold.ttf':(200,0),
          'DejaVuSerif-Italic.ttf':(80,100),'DejaVuSerif-BoldItalic.ttf':(200,100)}
for path in fonts:
    assert subprocess.check_output(['dpkg-query','-S',str(path)],text=True).startswith('dejavu-fonts: ')
    values=subprocess.check_output(['fc-query','-f','%{family}\n%{weight}\n%{slant}\n%{charset}\n',str(path)],text=True).splitlines()
    assert values[0]=='DejaVu Serif' and tuple(map(int,values[1:3]))==expected[path.name]
    ranges=[tuple(int(x,16) for x in token.split('-')) for token in values[3].split()]
    for point in [32,65,90,97,122,0xe3,0xe7,0x416,0x44f]:
        assert any(r[0]<=point<=r[-1] for r in ranges),(path.name,point)
resolved={f:subprocess.check_output(['fc-match','-f','%{family}',f],text=True) for f in ['serif','sans-serif','monospace']}
assert resolved=={'serif':'DejaVu Serif','sans-serif':'Adwaita Sans','monospace':'Adwaita Mono'},resolved
assert list(Path('/var/cache/fontconfig').glob('*.cache-*'))
PY
scratch=$(mktemp -d /tmp/toddy-serif.XXXXXX)
trap 'rm -rf "$scratch"' EXIT
cat > "$scratch/width.c" <<'C'
#include <ft2build.h>
#include FT_FREETYPE_H
int main(void) {
    FT_Library lib; FT_Face face;
    if (FT_Init_FreeType(&lib) || FT_New_Face(lib,"/usr/share/fonts/dejavu/DejaVuSerif.ttf",0,&face)) return 1;
    if (FT_Set_Char_Size(face,0,20*64,96,96)) return 2;
    if (FT_Load_Char(face,'i',FT_LOAD_DEFAULT)) return 3;
    FT_Pos narrow=face->glyph->advance.x;
    if (FT_Load_Char(face,'W',FT_LOAD_DEFAULT)) return 4;
    if (!(narrow>0 && face->glyph->advance.x>narrow)) return 5;
    FT_Done_Face(face); FT_Done_FreeType(lib); return 0;
}
C
cc $(pkg-config --cflags freetype2) "$scratch/width.c" -o "$scratch/width" $(pkg-config --libs freetype2)
"$scratch/width"
NATIVE
