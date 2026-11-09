#!/bin/bash
# Upstream declaration metadata only; never invoke the legacy GL function.
set -euo pipefail
[[ $(id -u) == 101 && -f /src/gir/GL-1.0.gir && -d /stage ]]
mkdir -p /stage/usr/share/gir-1.0 /stage/usr/lib/girepository-1.0
cp /src/gir/GL-1.0.gir /stage/usr/share/gir-1.0/
g-ir-compiler /stage/usr/share/gir-1.0/GL-1.0.gir --output=/stage/usr/lib/girepository-1.0/GL-1.0.typelib
GI_TYPELIB_PATH=/stage/usr/lib/girepository-1.0 python3 -B - <<'PY'
from pathlib import Path
import gi,hashlib,json,xml.etree.ElementTree as ET
gi.require_version('GL','1.0')
from gi.repository import GL
assert GL._version=='1.0'
source=Path('/src/gir/GL-1.0.gir');gir=Path('/stage/usr/share/gir-1.0/GL-1.0.gir');typelib=Path('/stage/usr/lib/girepository-1.0/GL-1.0.typelib')
assert source.read_bytes()==gir.read_bytes()
ns={'g':'http://www.gtk.org/introspection/core/1.0'};namespace=ET.fromstring(gir.read_bytes()).find('g:namespace',ns)
assert namespace.get('name')=='GL' and not namespace.get('shared-library')
assert len(namespace.findall('g:record',ns))==13 and len(namespace.findall('g:function',ns))==1
Path('/build/test-results.json').write_text(json.dumps({'scope':'Unchanged original GI1.86 GL namespace declarations/native typelib compilation/import only; not legacy GL function or GPU runtime acceptance','source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'typelib_sha256':hashlib.sha256(typelib.read_bytes()).hexdigest(),'native_compiler_exit':0,'native_import_exit':0,'records':13,'legacy_function_not_invoked':'glInitNames','upstream_suite':'Declarative GIR, no executable suite; no GL provider or foundation core rebuild'},indent=2)+'\n')
PY
