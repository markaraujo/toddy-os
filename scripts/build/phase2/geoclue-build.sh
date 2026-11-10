#!/bin/bash
set -euo pipefail
[[ $(id -u) == 101 && ! -e /build/compile ]]
export PYTHONDONTWRITEBYTECODE=1
meson setup /build/compile /src --prefix=/usr --sysconfdir=/etc --libdir=lib \
 --buildtype=release --wrap-mode=nodownload -Dc_std=gnu17 -Denable-backend=true \
 -Dlibgeoclue=true -Dintrospection=true -Dvapi=true -Dgtk-doc=false \
 -Dwifi-source=true -Dstatic-source=true -Dip-source=true -Dcompass=true \
 -D3g-source=false -Dcdma-source=false -Dmodem-gps-source=false -Dnmea-source=false \
 -Ddemo-agent=false -Ddbus-srv-user=geoclue \
 -Ddbus-sys-dir=/usr/share/dbus-1/system.d -Dsystemd-system-unit-dir=/usr/lib/systemd/system
ninja -C /build/compile -j4
meson introspect /build/compile --tests > /build/original-registered-tests.json
python3 - <<'PY'
import json
from pathlib import Path
assert json.loads(Path('/build/original-registered-tests.json').read_text())==[], 'Review newly registered original programs; do not skip them'
PY
meson install -C /build/compile --destdir /stage --no-rebuild
cc /src/toddy-probe.c -I/stage/usr/include/libgeoclue-2.0 -L/stage/usr/lib \
 $(pkg-config --cflags --libs gio-2.0) -lgeoclue-2 -lm -Wl,-rpath,/stage/usr/lib -o /build/native-probe
LD_LIBRARY_PATH=/stage/usr/lib /build/native-probe > /build/native-consumer.json
/stage/usr/libexec/geoclue --version > /build/daemon-version.txt
if /stage/usr/libexec/geoclue --toddy-invalid-option > /build/daemon-invalid.log 2>&1; then
 echo 'Invalid daemon CLI option unexpectedly accepted' >&2; exit 1
fi
python3 - <<'PY'
from pathlib import Path
import hashlib,json
p=Path('/build');assert '2.8.2' in (p/'daemon-version.txt').read_text()
r={'scope':'Full backend/convenience library/GI/Vala with WiFi/static/IP/compass; optional modem/NMEA/demo-agent/docs omitted. No registered upstream automated tests in exact source. Actual GObject/D-Bus typed skeleton/UTF8/type refusal/recovery and daemon CLI only; service authorization/provider/owner position/native GNOME pending.','compile_exit':0,'stage_exit':0,'original_registered_tests':[],'consumer':json.loads((p/'native-consumer.json').read_text()),'daemon_version':(p/'daemon-version.txt').read_text().strip(),'daemon_invalid_option_refused':True,'artifacts':{str(f.relative_to(p/'compile')):hashlib.sha256(f.read_bytes()).hexdigest() for f in (p/'compile').rglob('*') if f.is_file() and not f.is_symlink() and f.open('rb').read(4)==b'\x7fELF'},'stage_sha256':{str(f.relative_to(p/'stage')):hashlib.sha256(f.read_bytes()).hexdigest() for f in (p/'stage').rglob('*') if f.is_file() and not f.is_symlink()}}
(p/'stage-results.json').write_text(json.dumps(r,indent=2)+'\n')
PY
