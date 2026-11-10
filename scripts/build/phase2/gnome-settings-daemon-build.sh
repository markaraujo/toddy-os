#!/bin/bash
set -euo pipefail
[[ $(id -u) == 101 && ! -e /build/compile ]]
export PYTHONDONTWRITEBYTECODE=1
meson setup /build/compile /src --prefix=/usr --sysconfdir=/etc --libdir=lib --localstatedir=/var \
 --buildtype=release --wrap-mode=nodownload -Dsystemd=true -Dsystemd-units=true \
 -Delogind=false -Dalsa=true -Dgudev=true -Dnetwork_manager=true -Drfkill=true \
 -Dsmartcard=true -Dgcr3=false -Dcolord=true -Dusb-protection=true \
 -Dcups=false -Dwwan=false -Dxwayland=false -Dudev_dir=/usr/lib/udev
ninja -C /build/compile -j4
meson introspect /build/compile --tests > /build/original-registered-tests.json
set +e
meson test -C /build/compile --print-errorlogs -j2 > /build/original-tests.log 2>&1
result=$?
set -e
printf '%s\n' "$result" > /build/original-tests.exit
[[ $result == 0 ]]
meson install -C /build/compile --destdir /stage --no-rebuild
GSETTINGS_BACKEND=memory python3 /src/toddy-probe.py /build/compile/data > /build/native-consumer.json
for name in color power media-keys; do
 LD_LIBRARY_PATH=/stage/usr/lib/gnome-settings-daemon-50 /stage/usr/libexec/gsd-"$name" --help > /build/CLI-"$name"-help.log 2>&1
done
python3 - <<'PY'
from pathlib import Path
import hashlib,json
p=Path('/build');rows=[json.loads(x) for x in (p/'compile/meson-logs/testlog.json').read_text().splitlines() if x.strip()]
assert rows and all(r['result'] in ['OK','SKIP','EXPECTEDFAIL'] for r in rows)
r={'scope':'Frozen full Linux Systemd/ALSA/gudev/NM/rfkill/Gcr4/smartcard/colord/USB-protection profile; optional CUPS/WWAN/XWayland omitted. Original programs retain exact results and fixture scopes; own private compiled-schema/memory reset/enum refusal and three CLI help checks only. No stock cache/native service/power/audio/display/hardware/GNOME acceptance.','compile_exit':0,'stage_exit':0,'original_tests':[{k:r[k] for k in ['name','result','returncode']} for r in rows],'consumer':json.loads((p/'native-consumer.json').read_text()),'artifacts':{str(f.relative_to(p/'compile')):hashlib.sha256(f.read_bytes()).hexdigest() for f in (p/'compile').rglob('*') if f.is_file() and not f.is_symlink() and f.open('rb').read(4)==b'\x7fELF'},'stage_sha256':{str(f.relative_to(p/'stage')):hashlib.sha256(f.read_bytes()).hexdigest() for f in (p/'stage').rglob('*') if f.is_file() and not f.is_symlink()}}
(p/'stage-results.json').write_text(json.dumps(r,indent=2)+'\n')
PY
