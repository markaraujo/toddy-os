#!/bin/bash
set -euo pipefail
[[ $(id -u) == 101 && ! -e /build/compile ]]
export PYTHONDONTWRITEBYTECODE=1
ulimit -c 0
python3 - <<'PY'
import os
s=os.statvfs('/build');assert s.f_bavail*s.f_frsize>=256*1024**2
PY
meson setup /build/compile /src --prefix=/usr --libdir=lib --buildtype=release --wrap-mode=nofallback -Deditorconfig=enabled -Ddevelopment=false
ninja -C /build/compile -j4 > /build/original-build.log 2>&1
meson introspect /build/compile --tests > /build/original-registered-tests.json
meson test -C /build/compile --no-rebuild --print-errorlogs > /build/original-tests.log 2>&1
# Upstream registers AppStream metadata validation only, not graphical tests.
meson install -C /build/compile --destdir /stage --no-rebuild
/stage/usr/bin/gnome-text-editor --version > /build/actual-version.log
python3 - <<'PY'
from pathlib import Path
import hashlib,json,os,xml.etree.ElementTree as ET
from gi.repository import GLib
w=Path('/build');tests=json.loads((w/'original-registered-tests.json').read_text());assert len(tests)==1 and tests[0]['name']=='Validate appstream file'
results=[json.loads(l) for l in (w/'compile/meson-logs/testlog.json').read_text().splitlines() if l.strip()];assert len(results)==1 and results[0]['result']=='OK' and results[0]['returncode']==0
version=(w/'actual-version.log').read_text();assert '50.1' in version and 'GtkSourceView:' in version
options={o['name']:o['value'] for o in json.loads((w/'compile/meson-info/intro-buildoptions.json').read_text())};assert options['editorconfig']=='enabled'
file=Path('/stage/usr/share/applications/org.gnome.TextEditor.desktop');k=GLib.KeyFile();k.load_from_file(str(file),GLib.KeyFileFlags.NONE);assert k.get_string('Desktop Entry','Type')=='Application' and k.get_string('Desktop Entry','Exec').startswith('gnome-text-editor')
schemas=list(Path('/stage/usr/share/glib-2.0/schemas').glob('*.gschema.xml'));assert schemas
ids=[x.attrib['id'] for p in schemas for x in ET.parse(p).getroot().findall('schema')];assert 'org.gnome.TextEditor' in ids
s=os.statvfs(w);assert s.f_bavail*s.f_frsize>=256*1024**2
r={'scope':'GNOME Text Editor50.1 compiler/stage and actual headless --version/desktop entry/schema checks only. Default EditorConfig enabled with owned Libspelling/Enchant. Original AppStream metadata validation only; no native GUI/open/save/edit/navigation/focus/recovery acceptance yet.','compile_exit':0,'stage_exit':0,'original_registered_tests':tests,'original_tests':results,'consumer':{'version':version,'desktop_entry':True,'schema_ids':ids,'editorconfig_enabled':True,'graphical_editor_tested':False},'scratch_free_bytes':s.f_bavail*s.f_frsize,'artifacts':{str(p.relative_to(w/'compile')):hashlib.sha256(p.read_bytes()).hexdigest() for p in (w/'compile').rglob('*') if p.is_file() and not p.is_symlink() and p.open('rb').read(4)==b'\x7fELF'},'stage_sha256':{str(p.relative_to(w/'stage')):hashlib.sha256(p.read_bytes()).hexdigest() for p in (w/'stage').rglob('*') if p.is_file() and not p.is_symlink()}}
(w/'stage-results.json').write_text(json.dumps(r,indent=2)+'\n')
PY
