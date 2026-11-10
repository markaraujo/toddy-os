#!/bin/bash
set -euo pipefail
[[ $(id -u) == 101 && ! -e /build/compile ]]
export PYTHONDONTWRITEBYTECODE=1
meson setup /build/compile /src --prefix=/usr --sysconfdir=/etc --localstatedir=/var --libdir=lib \
 --buildtype=release --wrap-mode=nodownload -Ddist_version=ToddyOS \
 -Dsession_tracking=systemd -Dsuspend_resume=systemd -Dsession_tracking_consolekit=false \
 -Dpolkit=true -Dconfig_auth_polkit_default=true -Dsystemd_journal=true \
 -Dselinux=false -Dlibaudit=no -Dcrypto=gnutls -Dwifi=true -Diwd=false \
 -Dppp=false -Dmodem_manager=false -Dovs=false -Dnm_cloud_setup=false \
 -Dnmtui=false -Dnmcli=true -Dintrospection=true -Dvapi=true -Dqt=false \
 -Ddocs=false -Dman=false -Dtests=yes -Dlibpsl=true -Dconcheck=true \
 -Difupdown=false -Difcfg_rh=false -Dnbft=false -Dclat=false -Debpf=false \
 -Dconfig_dhcp_default=internal -Ddbus_conf_dir=/usr/share/dbus-1/system.d \
 -Dsystemdsystemunitdir=/usr/lib/systemd/system -Dsystemdsystemgeneratordir=/usr/lib/systemd/system-generators \
 -Dudev_dir=/usr/lib/udev -Druntime_dir=/run
ninja -C /build/compile -j4
meson introspect /build/compile --tests > /build/original-registered-tests.json
set +e
meson test -C /build/compile --print-errorlogs -j2 > /build/original-tests.log 2>&1
test_exit=$?
set -e
printf '%s\n' "$test_exit" > /build/original-tests.exit
[[ $test_exit == 0 ]]
meson install -C /build/compile --destdir /stage --no-rebuild
cc /src/toddy-probe.c -I/stage/usr/include/libnm -L/stage/usr/lib \
 $(pkg-config --cflags --libs gio-2.0) -lnm -Wl,-rpath,/stage/usr/lib -o /build/native-probe
LD_LIBRARY_PATH=/stage/usr/lib /build/native-probe > /build/native-consumer.json
python3 - <<'PY'
from pathlib import Path
import hashlib,json
p=Path('/build');rows=[json.loads(s) for s in (p/'compile/meson-logs/testlog.json').read_text().splitlines() if s.strip()]
assert rows and all(r['result'] in ['OK','SKIP','EXPECTEDFAIL'] for r in rows)
r={'scope':'Pinned NetworkManager full native daemon/libnm/nmcli/GI/Vala/WiFi/internal DHCP/polkit/systemd/GnuTLS/PSL/connectivity profile. Optional cellular/PPP/OVS/cloud/nmtui/Qt examples omitted. Original unprivileged programs retain individual skips/results. Own offline typed connection consumer, NOT actual daemon authorization/network/GNOME acceptance.','compile_exit':0,'stage_exit':0,'original_tests':[{k:r[k] for k in ['name','result','returncode']} for r in rows],'consumer':json.loads((p/'native-consumer.json').read_text()),'artifacts':{str(f.relative_to(p/'compile')):hashlib.sha256(f.read_bytes()).hexdigest() for f in (p/'compile').rglob('*') if f.is_file() and not f.is_symlink() and f.open('rb').read(4)==b'\x7fELF'},'stage_sha256':{str(f.relative_to(p/'stage')):hashlib.sha256(f.read_bytes()).hexdigest() for f in (p/'stage').rglob('*') if f.is_file() and not f.is_symlink()}}
(p/'stage-results.json').write_text(json.dumps(r,indent=2)+'\n')
PY
