#!/bin/bash
# Co-install the frozen Gcr3 C ABI required by GNOME Keyring50; preserve Gcr4.
set -euo pipefail
[[ $(id -u) == 101 && ! -e /build/compile ]]
export PYTHONDONTWRITEBYTECODE=1
export PATH=/src/toddy-test-sdk/bin:/usr/bin:/usr/sbin
meson setup /build/compile /src --prefix=/usr --libdir=lib --libexecdir=libexec \
    --sysconfdir=/etc --localstatedir=/var --buildtype=release --wrap-mode=nodownload \
    -Dintrospection=false -Dgtk=true -Dgtk_doc=false -Dssh_agent=false -Dsystemd=enabled
ninja -C /build/compile -j4
meson test -C /build/compile --no-rebuild --print-errorlogs -j2 \
    --suite egg --suite gck --suite gcr > /build/original-tests.log 2>&1
meson install -C /build/compile --destdir /stage --no-rebuild
cc /src/toddy-probe.c -I/stage/usr/include/gcr-3 -I/stage/usr/include/gck-1 -L/stage/usr/lib -lgcr-base-3 -lgck-1 $(pkg-config --cflags --libs gio-2.0 gobject-2.0 p11-kit-1) -Wl,-rpath,/stage/usr/lib -o /build/native-probe
LD_LIBRARY_PATH=/stage/usr/lib /build/native-probe > /build/native-consumer.json 2> /build/native-consumer.stderr
python3 - <<'PY'
from pathlib import Path
import hashlib,json,re
p=Path('/build');rows=[json.loads(s) for s in (p/'compile/meson-logs/testlog.json').read_text().splitlines() if s.strip()]
assert rows and all(r['result'] in ['OK','SKIP','EXPECTEDFAIL'] for r in rows)
assert any(r['result']=='OK' and r['returncode']==0 for r in rows)
registered=json.loads((p/'compile/meson-info/intro-tests.json').read_text())
result={'scope':'Co-installed Gcr3/Gck1 C ABI for Keyring; original core fixtures and native transport/refusal/recovery only. GTK3 UI original programs pending native display; optional legacy GI/Vala/docs/SSH-agent omitted, no graphical/real credential acceptance','compile_exit':0,'stage_exit':0,'registered_original_programs':len(registered),'selected_original_programs':len(rows),'original_tests':[{k:r[k] for k in ['name','result','returncode']} for r in rows],'original_nested_skips':[{'program':r['name'],'line':s} for r in rows for s in r.get('stdout','').splitlines() if re.match(r'^ok \d+.*#\s*SKIP',s,re.I)],'consumer':json.loads((p/'native-consumer.json').read_text()),'artifacts':{str(f.relative_to(p/'compile')):hashlib.sha256(f.read_bytes()).hexdigest() for f in (p/'compile').rglob('*') if f.is_file() and not f.is_symlink() and f.open('rb').read(4)==b'\x7fELF'},'stage_sha256':{str(f.relative_to(p/'stage')):hashlib.sha256(f.read_bytes()).hexdigest() for f in (p/'stage').rglob('*') if f.is_file() and not f.is_symlink()}}
assert not any('toddy-test-sdk' in name for name in result['stage_sha256'])
(p/'stage-results.json').write_text(json.dumps(result,indent=2)+'\n')
PY
