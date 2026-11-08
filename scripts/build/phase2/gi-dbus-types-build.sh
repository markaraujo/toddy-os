#!/bin/bash
# Add the upstream declarative DBus GIR omitted from B01's scanner bootstrap.
set -euo pipefail
[[ $(id -u) == 101 && -f /src/gir/DBus-1.0.gir && -d /stage ]]
mkdir -p /stage/usr/share/gir-1.0 /stage/usr/lib/girepository-1.0
cp /src/gir/DBus-1.0.gir /stage/usr/share/gir-1.0/
g-ir-compiler /stage/usr/share/gir-1.0/DBus-1.0.gir \
    --output=/stage/usr/lib/girepository-1.0/DBus-1.0.typelib
GI_TYPELIB_PATH=/stage/usr/lib/girepository-1.0 python3 -B - <<'PY'
from pathlib import Path
import hashlib,json,gi
gi.require_version('DBus','1.0')
from gi.repository import DBus
assert int(DBus.BusType.SESSION)==0 and int(DBus.BusType.SYSTEM)==1
source=Path('/src/gir/DBus-1.0.gir');gir=Path('/stage/usr/share/gir-1.0/DBus-1.0.gir');typelib=Path('/stage/usr/lib/girepository-1.0/DBus-1.0.typelib')
assert source.read_bytes()==gir.read_bytes()
Path('/build/test-results.json').write_text(json.dumps({'scope':'Unchanged declarative upstream DBus GIR/native compiler/Python enum consumer, no core rebuild or complete D-Bus/GUI claim',
    'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'typelib_sha256':hashlib.sha256(typelib.read_bytes()).hexdigest(),
    'native_compiler_exit':0,'native_enum_consumer_exit':0,'registered_tests':'Declarative metadata, no executable upstream suite'},indent=2)+'\n')
PY
