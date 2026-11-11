#!/bin/bash
# Invoke only after the successful compiler; this runs as UID101 in isolated.sh.
set -euo pipefail
[[ $(id -u) == 101 && -f /build/obj/config.status ]]
[[ ! -e /build/firefox-stage-result.json && ! -e /build/firefox-stage-1.log ]]
[[ -z $(ls -A /stage) && $(cat /src/browser/config/version.txt) == 153.7.0 ]]
ulimit -c 0
export PYTHONDONTWRITEBYTECODE=1
export PATH=/tools/nasm/usr/bin:/usr/bin:/usr/sbin
export CC=clang CXX=clang++
export WASM_CC=/tools/wasi-sdk/bin/clang WASM_CXX=/tools/wasi-sdk/bin/clang++
export MOZCONFIG=/build/mozconfig MOZBUILD_STATE_PATH=/build/mozbuild
export MACH_BUILD_PYTHON_NATIVE_PACKAGE_SOURCE=none CARGO_HOME=/build/cargo-home
export DESTDIR=/stage
unset MOZ_TELEMETRY_REPORTING
cd /build
python3 - <<'PY'
from pathlib import Path
import hashlib,json,os,shutil,subprocess,time
w=Path('/build');stage=Path('/stage')
compiled=json.loads((w/'firefox-compile-result-2.json').read_text())
assert compiled['state']=='compiled' and compiled['exit']==0 and not compiled['interrupted_for_reserve']
def digest(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
for name,sha in compiled['artifacts'].items():assert digest(w/'obj/dist/bin'/name)==sha
assert shutil.disk_usage(stage).free>=1024**3 and os.statvfs(stage).f_favail>=4096
r={'state':'staging','source_version':'153.7.0esr','compiled_artifacts':compiled['artifacts'],
   'compiler_result_sha256':digest(w/'firefox-compile-result-2.json'),
   'scope':'Upstream install to private DESTDIR only; no native package install or browser runtime acceptance'}
receipt=w/'firefox-stage-result.json'
def save():receipt.write_text(json.dumps(r,indent=2)+'\n')
save();started=time.monotonic()
with (w/'firefox-stage-1.log').open('xb') as log:
 q=subprocess.run(['/src/mach','install'],stdout=log,stderr=subprocess.STDOUT)
r.update(state='install-command-returned',stage_exit=q.returncode,elapsed_seconds=round(time.monotonic()-started,3));save()
assert q.returncode==0,r
runtime=stage/'usr/lib/firefox'
assert (runtime/'firefox').is_file() and (runtime/'libxul.so').is_file()
assert 'Version=153.7.0' in (runtime/'application.ini').read_text()
launcher=stage/'usr/bin/firefox'
assert launcher.is_symlink() and os.readlink(launcher)=='/usr/lib/firefox/firefox'
launcher.unlink();launcher.symlink_to('../lib/firefox/firefox')
app=stage/'usr/share/applications/firefox.desktop';app.parent.mkdir(parents=True,exist_ok=True)
assert not app.exists()
app.write_text('''[Desktop Entry]
Type=Application
Name=Web Browser
GenericName=Web Browser
Comment=Browse the web
Exec=firefox %u
TryExec=firefox
Icon=firefox
Terminal=false
Categories=GNOME;GTK;Network;WebBrowser;
MimeType=text/html;application/xhtml+xml;x-scheme-handler/http;x-scheme-handler/https;
StartupNotify=true
StartupWMClass=firefox
''');app.chmod(0o644)
icons={}
for size in [16,32,48,64,128]:
 src=runtime/f'browser/chrome/icons/default/default{size}.png'
 if not src.exists():continue
 assert src.is_file() and not src.is_symlink()
 dst=stage/f'usr/share/icons/hicolor/{size}x{size}/apps/firefox.png';dst.parent.mkdir(parents=True,exist_ok=True)
 shutil.copyfile(src,dst);dst.chmod(0o644);icons[str(size)]=digest(dst);assert digest(dst)==digest(src)
assert '128' in icons
# The pinned guest has GIO/PyGObject; desktop-file-utils is not installed.
# Parse through the actual native GLib consumer, then verify launcher use in GNOME.
import gi
from gi.repository import GLib
keyfile=GLib.KeyFile();keyfile.load_from_file(str(app),GLib.KeyFileFlags.NONE)
assert keyfile.get_string('Desktop Entry','Type')=='Application'
assert keyfile.get_string('Desktop Entry','Exec')=='firefox %u'
assert not keyfile.get_boolean('Desktop Entry','Terminal')
files=[p for p in stage.rglob('*') if p.is_file() and not p.is_symlink()]
size=sum(p.stat().st_size for p in files);assert len(files)<15000 and size<1024**3
r.update(state='staged',runtime_artifacts={n:digest(runtime/n) for n in ['firefox','libxul.so']},
         post_stage_compiler_artifacts={n:digest(w/'obj/dist/bin'/n) for n in compiled['artifacts']},
         desktop_sha256=digest(app),icon_sha256=icons,regular_files=len(files),stage_bytes=size)
save();print(json.dumps(r))
PY
