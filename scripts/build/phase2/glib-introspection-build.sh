#!/bin/bash
# Complete the same frozen GLib build after the scanner bootstrap is installed.
set -euo pipefail
[[ $(id -u) == 101 && -e /build/compile/build.ninja ]]
python3 - <<'BEFORE'
from pathlib import Path
import hashlib,json
libs={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in Path('/stage/usr/lib').glob('*.so.*') if not p.is_symlink()}
assert libs
Path('/build/introspection-before-libs.json').write_text(json.dumps(libs,sort_keys=True)+'\n')
BEFORE
meson configure /build/compile -Dintrospection=enabled
ninja -C /build/compile -j8
DESTDIR=/stage ninja -C /build/compile install
for namespace in GLib-2.0 GObject-2.0 Gio-2.0 GIRepository-3.0; do
    test -s "/stage/usr/lib/girepository-1.0/$namespace.typelib"
    test -s "/stage/usr/share/gir-1.0/$namespace.gir"
done
python3 - <<'VERIFY'
from pathlib import Path
import hashlib,json,subprocess
old=json.loads(Path('/build/introspection-before-libs.json').read_text())
new={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in Path('/stage/usr/lib').glob('*.so.*') if not p.is_symlink()}
same=old==new
if not same:
    subprocess.run(['meson','test','-C','/build/compile','--no-rebuild','--num-processes','4','--print-errorlogs',
      *['glib:'+s for s in ['mainloop','gvariant','asyncqueue','basics-gobject','properties','signals',
       'gdbus-message','gdbus-serialization','gdbus-introspection','gdbus-auth','gdbus-close-pending',
       'gdbus-proxy','gdbus-connection-loss','gdbus-method-invocation']]],check=True)
Path('/build/introspection-qualification.json').write_text(json.dumps({'unchanged_core_libraries':same,
    'before':old,'after':new,'core_checks':'reused identical libraries' if same else '14 affected groups rerun passed',
    'required_typelibs':['GLib-2.0','GObject-2.0','Gio-2.0','GIRepository-3.0']},indent=2)+'\n')
VERIFY
