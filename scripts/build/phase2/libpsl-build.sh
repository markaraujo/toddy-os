#!/bin/bash
set -euo pipefail
[[ $(id -u) == 101 && ! -e /build/compile ]]
export PYTHONDONTWRITEBYTECODE=1
# The supported ICU backend reuses the qualified shared Unicode runtime.
meson setup /build/compile /src --prefix=/usr --libdir=lib \
    --buildtype=release --wrap-mode=nodownload -Druntime=libicu \
    -Dbuiltin=true -Ddocs=false -Dtests=true
ninja -C /build/compile -j4
meson test -C /build/compile --print-errorlogs -j2 > /build/original-tests.log 2>&1
meson install -C /build/compile --destdir /stage --no-rebuild
cc /src/toddy-probe.c -I/stage/usr/include -L/stage/usr/lib -lpsl -Wl,-rpath,/stage/usr/lib -o /build/native-probe
/build/native-probe > /build/native-consumer.json
python3 - <<'PY'
from pathlib import Path
import hashlib,json
p=Path('/build');rows=[json.loads(s) for s in (p/'compile/meson-logs/testlog.json').read_text().splitlines() if s.strip()]
assert len(rows)==8 and all(r['result']=='OK' and r['returncode']==0 for r in rows)
result={'scope':'Original public suffix/cookie/Unicode programs and actual ICU/private runtime-list/refusal/recovery; no browser/HTTP/network acceptance','compile_exit':0,'stage_exit':0,'IDNA_backend':'Owned ICU78.3; upstream-supported libicu option','original_tests':[{k:r[k] for k in ['name','result','returncode']} for r in rows],'consumer':json.loads((p/'native-consumer.json').read_text()),'artifacts':{str(f.relative_to(p/'compile')):hashlib.sha256(f.read_bytes()).hexdigest() for f in (p/'compile').rglob('*') if f.is_file() and not f.is_symlink() and f.open('rb').read(4)==b'\x7fELF'},'stage_sha256':{str(f.relative_to(p/'stage')):hashlib.sha256(f.read_bytes()).hexdigest() for f in (p/'stage').rglob('*') if f.is_file() and not f.is_symlink()}}
(p/'stage-results.json').write_text(json.dumps(result,indent=2)+'\n')
PY
