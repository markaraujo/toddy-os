#!/bin/bash
set -euo pipefail
[[ $(id -u) == 101 && ! -e /build/compile ]]
export PYTHONDONTWRITEBYTECODE=1
meson setup /build/compile /src --prefix=/usr --libdir=lib --libexecdir=libexec \
    --sysconfdir=/etc --localstatedir=/var --buildtype=release --wrap-mode=nodownload \
    -Dman=false -Ddocbook=false
ninja -C /build/compile -j4
meson install -C /build/compile --destdir /stage --no-rebuild
mkdir /build/schema-private
cp /stage/usr/share/glib-2.0/schemas/*.gschema.xml /build/schema-private/
glib-compile-schemas --strict /build/schema-private
python3 /src/toddy-probe.py /stage /build/schema-private > /build/native-consumer.json
python3 - <<'PY'
from pathlib import Path
import hashlib,json
p=Path('/build');registered=json.loads((p/'compile/meson-info/intro-tests.json').read_text());assert registered==[]
result={'scope':'Native staged GNOME session CLI/schema/layout; upstream provides a manually invoked test-client-dbus but no registered automated tests. No real session/login/GUI acceptance','compile_exit':0,'stage_exit':0,'registered_original_tests':0,'manual_client':'Built uninstalled test-client-dbus; run only against actual native session later','consumer':json.loads((p/'native-consumer.json').read_text()),'artifacts':{str(f.relative_to(p/'compile')):hashlib.sha256(f.read_bytes()).hexdigest() for f in (p/'compile').rglob('*') if f.is_file() and not f.is_symlink() and f.open('rb').read(4)==b'\x7fELF'},'stage_sha256':{str(f.relative_to(p/'stage')):hashlib.sha256(f.read_bytes()).hexdigest() for f in (p/'stage').rglob('*') if f.is_file() and not f.is_symlink()}}
(p/'stage-results.json').write_text(json.dumps(result,indent=2)+'\n')
PY
