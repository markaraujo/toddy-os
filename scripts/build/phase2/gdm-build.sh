#!/bin/bash
set -euo pipefail
[[ $(id -u) == 101 && ! -e /build/compile && -d /src/toddy-test-sdk ]]
export PYTHONDONTWRITEBYTECODE=1
ln -s /src/toddy-test-sdk /build/test-sdk
export PKG_CONFIG_PATH=/build/test-sdk/lib/pkgconfig
export LD_LIBRARY_PATH=/build/test-sdk/lib
meson setup /build/compile /src --prefix=/usr --libdir=lib --sysconfdir=/etc --localstatedir=/var \
 --buildtype=release --wrap-mode=nodownload -Dx11-support=false -Dgdm-xsession=false \
 -Ddefault-pam-config=lfs -Ddistro=lfs -Dlogind-provider=systemd \
 -Dsystemd-journal=true -Dselinux=disabled -Dlibaudit=disabled -Dplymouth=disabled \
 -Ddbus-sys=/usr/share/dbus-1/system.d -Dpam-prefix=/etc -Dpam-mod-dir=/usr/lib/security \
 -Dsystemdsystemunitdir=/usr/lib/systemd/system -Dsystemduserunitdir=/usr/lib/systemd/user \
 -Dworking-dir=/var/lib/gdm -Dat-spi-registryd-dir=/usr/libexec
ninja -C /build/compile -j4
meson introspect /build/compile --tests > /build/original-registered-tests.json
meson test -C /build/compile --print-errorlogs -j1 > /build/original-tests.log 2>&1
meson install -C /build/compile --destdir /stage --no-rebuild
cc /src/toddy-probe.c -I/stage/usr/include/gdm -L/stage/usr/lib \
 $(pkg-config --cflags --libs gio-2.0) -lgdm -Wl,-rpath,/stage/usr/lib -o /build/native-probe
LD_LIBRARY_PATH=/stage/usr/lib:/build/test-sdk/lib /build/native-probe > /build/native-consumer.json
LD_LIBRARY_PATH=/stage/usr/lib /stage/usr/sbin/gdm --version > /build/daemon-version.log 2>&1
python3 - <<'PY'
from pathlib import Path
import hashlib,json
p=Path('/build');rows=[json.loads(x) for x in (p/'compile/meson-logs/testlog.json').read_text().splitlines() if x.strip()]
assert len(rows)==1 and rows[0]['name']=='gdm:m-common' and rows[0]['result']=='OK' and rows[0]['returncode']==0
assert '50.2' in (p/'daemon-version.log').read_text()
r={'scope':'Frozen GDM50.2 with actual Wayland local login daemon/full PAM/Systemd/journal/libgdm/GI/pam_gdm; supported X11 path and optional SELinux/audit/Plymouth omitted. Reused qualified private CheckSDK only for one original m-common driver. Own client/extension ownership/precancel/refusal/recovery/CLI only; actual account/greeter/PAM/keyring/privilege/login/desktop/cache gates pending.','compile_exit':0,'stage_exit':0,'original_tests':[{k:r[k] for k in ['name','result','returncode']} for r in rows],'consumer':json.loads((p/'native-consumer.json').read_text()),'daemon_version':(p/'daemon-version.log').read_text().strip(),'artifacts':{str(f.relative_to(p/'compile')):hashlib.sha256(f.read_bytes()).hexdigest() for f in (p/'compile').rglob('*') if f.is_file() and not f.is_symlink() and f.open('rb').read(4)==b'\x7fELF'},'stage_sha256':{str(f.relative_to(p/'stage')):hashlib.sha256(f.read_bytes()).hexdigest() for f in (p/'stage').rglob('*') if f.is_file() and not f.is_symlink()}}
(p/'stage-results.json').write_text(json.dumps(r,indent=2)+'\n')
PY
