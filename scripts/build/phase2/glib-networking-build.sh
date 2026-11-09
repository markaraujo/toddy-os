#!/bin/bash
set -euo pipefail
[[ $(id -u) == 101 && ! -e /build/compile ]]
export PYTHONDONTWRITEBYTECODE=1
meson setup /build/compile /src --prefix=/usr --libdir=lib \
    --buildtype=release --wrap-mode=nodownload -Dgnutls=enabled \
    -Dopenssl=disabled -Dlibproxy=enabled -Dgnome_proxy=enabled \
    -Denvironment_proxy=disabled -Dinstalled_tests=false -Ddebug_logs=false
ninja -C /build/compile -j4
meson test -C /build/compile --print-errorlogs -j1 > /build/original-tests.log 2>&1
meson install -C /build/compile --destdir /stage --no-rebuild
# Stage-local discovery cache only. The installed shared DConf/GIO cache needs
# a separate controlled native regeneration after module ownership promotion.
gio-querymodules /stage/usr/lib/gio/modules
cc /src/toddy-probe.c $(pkg-config --cflags --libs gio-2.0) -o /build/native-probe
GIO_MODULE_DIR=/stage/usr/lib/gio/modules GIO_USE_TLS=gnutls /build/native-probe > /build/native-consumer.json
python3 - <<'PY'
from pathlib import Path
import hashlib,json
p=Path('/build');tests=[json.loads(s) for s in (p/'compile/meson-logs/testlog.json').read_text().splitlines() if s.strip()]
assert len(tests)==6 and all(r['result']=='OK' and r['returncode']==0 for r in tests)
assert any('connection-gnutls-tls1.2' in r['name'] for r in tests)
result={'scope':'Six original GNOME/libproxy/certificate/database/TLS1.3-default/TLS1.2 drivers with private loopback and upstream PKCS11 test fixture. Actual public GIO backend/default factory-root verification/malformed certificate refusal/recovery. DTLS disabled upstream; remote network/native GNOME pending.', 'compile_exit':0,'stage_exit':0,'original_tests':[{k:r[k] for k in ['name','result','returncode']} for r in tests], 'consumer':json.loads((p/'native-consumer.json').read_text()), 'artifacts':{str(f.relative_to(p/'compile')):hashlib.sha256(f.read_bytes()).hexdigest() for f in (p/'compile').rglob('*') if f.is_file() and not f.is_symlink() and f.open('rb').read(4)==b'\x7fELF'}, 'stage_sha256':{str(f.relative_to(p/'stage')):hashlib.sha256(f.read_bytes()).hexdigest() for f in (p/'stage').rglob('*') if f.is_file() and not f.is_symlink()}}
(p/'stage-results.json').write_text(json.dumps(result,indent=2)+'\n')
PY
