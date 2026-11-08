#!/bin/bash
# Unmodified proportional serif fallback, not a UI font/theme replacement.
set -euo pipefail
[[ $(id -u) == 101 && -d /stage && ! -e /stage/usr ]]
install -d -m755 /stage/usr/share/fonts/dejavu
for style in '' -Bold -Italic -BoldItalic; do
    install -m644 "/src/ttf/DejaVuSerif${style}.ttf" /stage/usr/share/fonts/dejavu/
done
python3 - <<'PY'
import hashlib,json,subprocess
from pathlib import Path
fonts=sorted(Path('/stage/usr/share/fonts/dejavu').glob('*.ttf'));assert len(fonts)==4
rows=[]
for font in fonts:
    assert font.read_bytes()==(Path('/src/ttf')/font.name).read_bytes()
    family=subprocess.check_output(['fc-query','-f','%{family}',str(font)],text=True)
    assert family=='DejaVu Serif'
    rows.append({'file':font.name,'sha256':hashlib.sha256(font.read_bytes()).hexdigest()})
Path('/build/font-inputs.json').write_text(json.dumps({'fonts':rows,'source_fonts_byte_identical':True,'upstream_suite':'Official data-only TTF release; no executable upstream suite','selection':'Four original DejaVuSerif faces, preserve Adwaita Sans/Mono and user font preferences'},indent=2)+'\n')
PY
