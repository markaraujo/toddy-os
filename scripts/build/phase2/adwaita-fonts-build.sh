#!/bin/bash
set -euo pipefail
[[ $(id -u) == 101 && -d /stage ]]
meson setup /build/compile /src --prefix=/usr --wrap-mode=nofallback
ninja -C /build/compile
DESTDIR=/stage ninja -C /build/compile install
python3 - <<'PY'
import hashlib,json
from pathlib import Path
source=Path('/src');stage=Path('/stage/usr/share/fonts/Adwaita')
fonts=list(stage.glob('*.ttf'));assert len(fonts)==6
rows=[]
for installed in sorted(fonts):
    originals=list(source.glob('*/'+installed.name));assert len(originals)==1
    assert originals[0].read_bytes()==installed.read_bytes()
    rows.append({'file':installed.name,'sha256':hashlib.sha256(installed.read_bytes()).hexdigest()})
Path('/build/font-inputs.json').write_text(json.dumps({'fonts':rows,'source_fonts_byte_identical':True,'upstream_suite':'data-only project; no upstream test suite'},indent=2)+'\n')
PY
