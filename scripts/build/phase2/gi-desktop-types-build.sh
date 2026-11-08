#!/bin/bash
# Selected declarative types omitted by the qualified B01 scanner-only bootstrap.
set -euo pipefail
[[ $(id -u) == 101 && -d /src/gir && -d /stage ]]
mkdir -p /stage/usr/share/gir-1.0 /stage/usr/lib/girepository-1.0
python3 - <<'TYPES'
from pathlib import Path
import hashlib,json,subprocess
names=['freetype2-2.0','fontconfig-2.0','libxml2-2.0','cairo-1.0']
rows=[]
for name in names:
    source=Path('/src/gir')/(name+('.gir.in' if name=='cairo-1.0' else '.gir'))
    original=source.read_bytes();data=original
    if name=='cairo-1.0':
        assert data.count(b'@CAIRO_SHARED_LIBRARY@')==data.count(b'@CAIRO_GIR_PACKAGE@')==1
        data=data.replace(b'@CAIRO_SHARED_LIBRARY@',b'libcairo-gobject.so.2').replace(b'@CAIRO_GIR_PACKAGE@',b'cairo-gobject')
    gir=Path('/stage/usr/share/gir-1.0')/(name+'.gir');gir.write_bytes(data)
    typelib=Path('/stage/usr/lib/girepository-1.0')/(name+'.typelib')
    subprocess.run(['g-ir-compiler','--includedir=/stage/usr/share/gir-1.0',str(gir),'--output='+str(typelib)],check=True)
    rows.append({'name':name,'source_sha256':hashlib.sha256(original).hexdigest(),'configured_gir_sha256':hashlib.sha256(data).hexdigest(),'typelib_sha256':hashlib.sha256(typelib.read_bytes()).hexdigest()})
Path('/build/test-results.json').write_text(json.dumps({'scope':'four selected upstream declarative GIR types compiled; no GI/core rebuild','types':rows},indent=2)+'\n')
TYPES
