#!/bin/bash
set -euo pipefail
[[ $(id -u) == 101 && ! -e /build/compile ]]
export PYTHONDONTWRITEBYTECODE=1
meson setup /build/compile /src --prefix=/usr --libdir=lib --libexecdir=libexec \
    --sysconfdir=/etc --localstatedir=/var --buildtype=release --wrap-mode=nodownload \
    -Dintrospection=true -Dvapi=false -Dgtk4=true -Dgtk_doc=false \
    -Dcrypto=libgcrypt -Dssh_agent=false -Dsystemd=enabled
ninja -C /build/compile -j4
meson test -C /build/compile --no-rebuild --print-errorlogs -j2 > /build/original-tests.log 2>&1
meson install -C /build/compile --destdir /stage --no-rebuild
export PKG_CONFIG_PATH=/stage/usr/lib/pkgconfig
cc /src/toddy-probe.c -I/stage/usr/include/gcr-4 -I/stage/usr/include/gck-2 -L/stage/usr/lib -lgcr-4 -lgck-2 $(pkg-config --cflags --libs gio-2.0 gobject-2.0 p11-kit-1) -Wl,-rpath,/stage/usr/lib -o /build/native-probe
LD_LIBRARY_PATH=/stage/usr/lib /build/native-probe > /build/native-consumer.json 2> /build/native-consumer.stderr
LD_LIBRARY_PATH=/stage/usr/lib GI_TYPELIB_PATH=/stage/usr/lib/girepository-1.0 python3 - <<'PY' > /build/native-gi.json
import gi,json
gi.require_version('Gcr','4');gi.require_version('Gck','2')
from gi.repository import Gcr,Gck
assert Gcr.SecretExchange.__gtype__.name=='GcrSecretExchange' and Gck.Module.__gtype__.name=='GckModule'
print(json.dumps({'native_gi_types':['GcrSecretExchange','GckModule'],'scope':'GI types only; native graphical credential prompt pending'}))
PY
python3 - <<'PY'
from pathlib import Path
import hashlib,json,re
p=Path('/build');rows=[json.loads(s) for s in (p/'compile/meson-logs/testlog.json').read_text().splitlines() if s.strip()]
assert rows and all(r['result'] in ['OK','SKIP','EXPECTEDFAIL'] for r in rows)
assert any(r['result']=='OK' and r['returncode']==0 for r in rows)
result={'scope':'Original Gcr/Gck/egg fixtures and actual transport/GI/refusal/recovery; no graphical prompt/keyring/real credential acceptance. Optional SSH-agent/Vala/docs excluded via upstream flags','compile_exit':0,'stage_exit':0,'original_tests':[{k:r[k] for k in ['name','result','returncode']} for r in rows],'original_nested_skips':[{'program':r['name'],'line':s} for r in rows for s in r.get('stdout','').splitlines() if re.match(r'^ok \d+.*#\s*SKIP',s,re.I)],'consumer':json.loads((p/'native-consumer.json').read_text()),'gi':json.loads((p/'native-gi.json').read_text()),'artifacts':{str(f.relative_to(p/'compile')):hashlib.sha256(f.read_bytes()).hexdigest() for f in (p/'compile').rglob('*') if f.is_file() and not f.is_symlink() and f.open('rb').read(4)==b'\x7fELF'},'stage_sha256':{str(f.relative_to(p/'stage')):hashlib.sha256(f.read_bytes()).hexdigest() for f in (p/'stage').rglob('*') if f.is_file() and not f.is_symlink()}}
(p/'stage-results.json').write_text(json.dumps(result,indent=2)+'\n')
PY
