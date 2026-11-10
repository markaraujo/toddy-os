#!/bin/bash
set -euo pipefail
[[ $(id -u) == 101 && ! -e /build/compile ]]
export PYTHONDONTWRITEBYTECODE=1
ulimit -c 0
meson setup /build/compile /src --prefix=/usr --libdir=lib --libexecdir=libexec \
 --sysconfdir=/etc --buildtype=release --wrap-mode=nofallback \
 -Dgtk3=true -Dgtk4=false -Dapp=false -Dglade=false -Ddocs=false \
 -Dgir=true -Dvapi=true -Da11y=true -Dfribidi=true -Dicu=true -Dgnutls=true \
 -D_systemd=true -Dterminfo=false
ninja -C /build/compile -j4
meson introspect /build/compile --tests > /build/original-registered-tests.json
set +e
meson test -C /build/compile --print-errorlogs -j2 > /build/original-tests.log 2>&1
result=$?
set -e
printf '%s\n' "$result" > /build/original-tests.exit
[[ $result == 0 ]]
meson install -C /build/compile --destdir /stage --no-rebuild
python3 - <<'PY'
from pathlib import Path
import hashlib,json,difflib
p=Path('/stage/etc/profile.d/vte.sh');before=p.read_bytes();text=before.decode()
old='    else\n        PROMPT_COMMAND="__vte_prompt_command"\n    fi'
new='    else\n        if [[ -n "${PROMPT_COMMAND:-}" ]]; then\n            PROMPT_COMMAND=("${PROMPT_COMMAND}" __vte_precmd __vte_osc7)\n        else\n            PROMPT_COMMAND="__vte_prompt_command"\n        fi\n    fi'
assert text.count(old)==1;p.write_text(text.replace(old,new))
source=Path('/src/src/vte.sh.in').read_text();assert source.count(old)==1
patch=''.join(difflib.unified_diff(source.splitlines(keepends=True),source.replace(old,new).splitlines(keepends=True),fromfile='a/src/vte.sh.in',tofile='b/src/vte.sh.in'))
doc=Path('/stage/usr/share/doc/vte');doc.mkdir(parents=True,exist_ok=True);(doc/'preserve-user-prompt-command.patch').write_text(patch)
Path('/build/shell-integration-selection.json').write_text(json.dumps({'scope':'Preserve existing non-array Bash PROMPT_COMMAND as exact first array entry, append native VTE callbacks; visible owner prompt preserved. Stock empty prompt behavior/source parser tests unchanged. No user files/fonts/shell framework overwritten.','before_sha256':hashlib.sha256(before).hexdigest(),'after_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'patch_sha256':hashlib.sha256(patch.encode()).hexdigest()},indent=2)+'\n')
PY
cc /src/toddy-probe.c -I/stage/usr/include/vte-2.91 -L/stage/usr/lib \
 $(pkg-config --cflags --libs gtk+-3.0 gio-2.0) -lvte-2.91 \
 -Wl,-rpath,/stage/usr/lib -o /build/native-probe
LD_LIBRARY_PATH=/stage/usr/lib /build/native-probe /stage/etc/profile.d/vte.sh > /build/native-consumer.json
GI_TYPELIB_PATH=/stage/usr/lib/girepository-1.0 LD_LIBRARY_PATH=/stage/usr/lib python3 - <<'PY' > /build/GI-consumer.json
import gi,json
gi.require_version('Vte','2.91')
from gi.repository import Vte
assert (Vte.get_major_version(),Vte.get_minor_version(),Vte.get_micro_version())==(0,84,1)
print(json.dumps({'namespace':'Vte2.91','runtime_version':'0.84.1','widget_or_display_tested':False}))
PY
python3 - <<'PY'
from pathlib import Path
import hashlib,json
p=Path('/build');rows=[json.loads(x) for x in (p/'compile/meson-logs/testlog.json').read_text().splitlines() if x.strip()]
assert rows and all(r['result'] in ['OK','SKIP','EXPECTEDFAIL'] for r in rows)
r={'scope':'Frozen VTE0.84.1 GTK3/API2.91 for GNOME Terminal, a11y/FriBidi/ICU/GnuTLS/GI/Vala/Systemd. Optional GTK4 widget/demo/Glade/docs/experimental terminfo omitted. Original tests retained; actual regex/refusal/PTYShell/geometry/UTF8/managed-group Stop/fresh recovery/interactive owner prompt preservation/C-GI only, no widget/desktop/GNOME Terminal/focus acceptance.','compile_exit':0,'stage_exit':0,'original_tests':[{k:r[k] for k in ['name','result','returncode']} for r in rows],'consumer':json.loads((p/'native-consumer.json').read_text()),'GI_consumer':json.loads((p/'GI-consumer.json').read_text()),'shell_integration':json.loads((p/'shell-integration-selection.json').read_text()),'artifacts':{str(f.relative_to(p/'compile')):hashlib.sha256(f.read_bytes()).hexdigest() for f in (p/'compile').rglob('*') if f.is_file() and not f.is_symlink() and f.open('rb').read(4)==b'\x7fELF'},'stage_sha256':{str(f.relative_to(p/'stage')):hashlib.sha256(f.read_bytes()).hexdigest() for f in (p/'stage').rglob('*') if f.is_file() and not f.is_symlink()}}
(p/'stage-results.json').write_text(json.dumps(r,indent=2)+'\n')
PY
