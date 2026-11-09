#!/bin/bash
set -euo pipefail
[[ $(id -u) == 101 && ! -e /build/compile ]]
export PYTHONDONTWRITEBYTECODE=1
meson setup /build/compile /src --prefix=/usr --libdir=lib --libexecdir=libexec \
    --sysconfdir=/etc --localstatedir=/var --buildtype=release --wrap-mode=nodownload \
    -Dtrust_paths=/etc/pki/anchors -Dtrust_module=enabled -Dlibffi=enabled \
    -Dsystemd=enabled -Dtest=true -Dgtk_doc=false -Dman=false
ninja -C /build/compile -j4
meson test -C /build/compile --no-rebuild --print-errorlogs -j2 > /build/original-tests.log 2>&1
meson install -C /build/compile --destdir /stage --no-rebuild
cc /src/toddy-probe.c -I/stage/usr/include/p11-kit-1 -L/stage/usr/lib -lp11-kit -Wl,-rpath,/stage/usr/lib -o /build/native-probe
/build/native-probe > /build/native-consumer.json
python3 - <<'PY'
from pathlib import Path
import hashlib,json
p=Path('/build');rows=[json.loads(s) for s in (p/'compile/meson-logs/testlog.json').read_text().splitlines() if s.strip()]
assert rows and all(r['result'] in ['OK','SKIP','EXPECTEDFAIL'] for r in rows)
assert any(r['result']=='OK' and r['returncode']==0 for r in rows)
result={'scope':'Original PKCS11/trust fixture programs and typed URI/refusal/recovery API consumer only; fixtures are not real credentials, hardware tokens or installed root-store acceptance','compile_exit':0,'stage_exit':0,'original_tests':[{k:r[k] for k in ['name','result','returncode']} for r in rows],'consumer':json.loads((p/'native-consumer.json').read_text()),'artifacts':{str(f.relative_to(p/'compile')):hashlib.sha256(f.read_bytes()).hexdigest() for f in (p/'compile').rglob('*') if f.is_file() and not f.is_symlink() and f.open('rb').read(4)==b'\x7fELF'},'stage_sha256':{str(f.relative_to(p/'stage')):hashlib.sha256(f.read_bytes()).hexdigest() for f in (p/'stage').rglob('*') if f.is_file() and not f.is_symlink()}}
(p/'stage-results.json').write_text(json.dumps(result,indent=2)+'\n')
PY
