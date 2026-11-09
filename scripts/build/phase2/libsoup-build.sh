#!/bin/bash
set -euo pipefail
[[ $(id -u) == 101 && ! -e /build/compile ]]
export PYTHONDONTWRITEBYTECODE=1
meson setup /build/compile /src --prefix=/usr --libdir=lib \
    --buildtype=release --wrap-mode=nodownload -Dtls_check=true \
    -Dintrospection=enabled -Dvapi=disabled -Ddocs=disabled \
    -Dtests=true -Dinstalled_tests=false -Dpkcs11_tests=enabled \
    -Dgssapi=disabled -Dntlm=disabled -Dbrotli=disabled \
    -Dsysprof=disabled -Dautobahn=disabled -Dfuzzing=disabled
ninja -C /build/compile -j4
meson test -C /build/compile --print-errorlogs -j2 > /build/original-tests.log 2>&1
meson install -C /build/compile --destdir /stage --no-rebuild
cc /src/toddy-probe.c -I/stage/usr/include/libsoup-3.0 -L/stage/usr/lib \
    $(pkg-config --cflags --libs gio-2.0) -lsoup-3.0 \
    -Wl,-rpath,/stage/usr/lib -o /build/native-probe
timeout 60s /build/native-probe > /build/native-consumer.json
python3 - <<'PY'
from pathlib import Path
import hashlib,json
p=Path('/build');tests=[json.loads(s) for s in (p/'compile/meson-logs/testlog.json').read_text().splitlines() if s.strip()]
assert tests and all(t['result'] in ['OK','SKIP'] and t['returncode'] in [0,77] for t in tests)
names={t['name'].split(':')[-1] for t in tests}
for name in ['ssl','http2','header-parsing','cookies','session','timeout','redirect','range']:
    assert name in names or name+'-test' in names,name
result={'scope':'Enabled original HTTP1/HTTP2/TLS/cookie/parser/redirect/cancellation/timeout drivers with private loopback, no external route. Apache/Autobahn/optional-auth/Brotli unavailable; all skips retained. Actual public HTTP client/server/precancel/no-dispatch/recovery/native SDK consumer, not remote network/browser/GNOME acceptance.', 'compile_exit':0,'stage_exit':0,'original_tests':[{k:t[k] for k in ['name','result','returncode']} for t in tests], 'consumer':json.loads((p/'native-consumer.json').read_text()), 'artifacts':{str(f.relative_to(p/'compile')):hashlib.sha256(f.read_bytes()).hexdigest() for f in (p/'compile').rglob('*') if f.is_file() and not f.is_symlink() and f.open('rb').read(4)==b'\x7fELF'}, 'stage_sha256':{str(f.relative_to(p/'stage')):hashlib.sha256(f.read_bytes()).hexdigest() for f in (p/'stage').rglob('*') if f.is_file() and not f.is_symlink()}}
(p/'stage-results.json').write_text(json.dumps(result,indent=2)+'\n')
PY
