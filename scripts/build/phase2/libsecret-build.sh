#!/bin/bash
set -euo pipefail
[[ $(id -u) == 101 && ! -e /build/compile ]]
export PYTHONDONTWRITEBYTECODE=1
meson setup /build/compile /src --prefix=/usr --libdir=lib --libexecdir=libexec \
    --sysconfdir=/etc --localstatedir=/var --buildtype=release --wrap-mode=nodownload \
    -Dintrospection=true -Dvapi=false -Dgtk_doc=false -Dmanpage=false \
    -Dcrypto=libgcrypt -Dtpm2=false -Dpam=false -Ddebugging=false
ninja -C /build/compile -j4
meson test -C /build/compile --no-rebuild --print-errorlogs -j2 > /build/original-tests.log 2>&1
meson install -C /build/compile --destdir /stage --no-rebuild
cc /src/toddy-probe.c -I/stage/usr/include/libsecret-1 -L/stage/usr/lib -lsecret-1 $(pkg-config --cflags --libs gio-2.0 gobject-2.0) -Wl,-rpath,/stage/usr/lib -o /build/native-probe
LD_LIBRARY_PATH=/stage/usr/lib /build/native-probe > /build/native-consumer.json
LD_LIBRARY_PATH=/stage/usr/lib GI_TYPELIB_PATH=/stage/usr/lib/girepository-1.0 python3 - <<'PY' > /build/native-gi.json
import gi,json
gi.require_version('Secret','1')
from gi.repository import Secret
assert Secret.Value.__gtype__.name=='SecretValue' and Secret.Service.__gtype__.name=='SecretService'
print(json.dumps({'native_gi_types':['SecretValue','SecretService'],'scope':'GI types only; actual keyring/provider integration pending'}))
PY
python3 - <<'PY'
from pathlib import Path
import hashlib,json,re
p=Path('/build');rows=[json.loads(s) for s in (p/'compile/meson-logs/testlog.json').read_text().splitlines() if s.strip()]
assert rows and all(r['result'] in ['OK','SKIP','EXPECTEDFAIL'] for r in rows)
assert any(r['result']=='OK' and r['returncode']==0 for r in rows)
result={'scope':'Original libsecret fixture programs and native binary/schema/refusal/lifecycle/GI consumer only; no actual installed keyring/real credential/provider/graphical acceptance','compile_exit':0,'stage_exit':0,'original_tests':[{k:r[k] for k in ['name','result','returncode']} for r in rows],'original_nested_skips':[{'program':r['name'],'line':s} for r in rows for s in r.get('stdout','').splitlines() if re.match(r'^ok \d+.*#\s*SKIP',s,re.I)],'consumer':json.loads((p/'native-consumer.json').read_text()),'gi':json.loads((p/'native-gi.json').read_text()),'artifacts':{str(f.relative_to(p/'compile')):hashlib.sha256(f.read_bytes()).hexdigest() for f in (p/'compile').rglob('*') if f.is_file() and not f.is_symlink() and f.open('rb').read(4)==b'\x7fELF'},'stage_sha256':{str(f.relative_to(p/'stage')):hashlib.sha256(f.read_bytes()).hexdigest() for f in (p/'stage').rglob('*') if f.is_file() and not f.is_symlink()}}
(p/'stage-results.json').write_text(json.dumps(result,indent=2)+'\n')
PY
