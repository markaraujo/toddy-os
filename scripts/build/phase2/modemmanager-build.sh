#!/bin/bash
set -euo pipefail
[[ $(id -u) == 101 && ! -e /build/compile ]]
export PYTHONDONTWRITEBYTECODE=1
ulimit -c 0
meson setup /build/compile /src --prefix=/usr --libdir=lib --sysconfdir=/etc --localstatedir=/var --buildtype=release --wrap-mode=nofallback -Dbash_completion=false -Dqrtr=false -Dpolkit=strict -Dmbim=true -Dqmi=true -Dintrospection=true
ninja -C /build/compile -j4 > /build/original-build.log 2>&1
meson introspect /build/compile --tests > /build/original-registered-tests.json
python3 - <<'PY'
from pathlib import Path
import json,subprocess
w=Path('/build');registered=json.loads((w/'original-registered-tests.json').read_text())
# Serial tests need a separately qualified PTY profile; stub needs a session bus.
# Compile them unchanged, preserve their inventory, and execute local parsers now.
deferred={'test-at-serial-port','test-qcdm-serial-port','test-stub'}
selected=[t['name'] for t in registered if t['name'] not in deferred]
assert len(selected)>=12 and {'test-pco','test-common-helpers','test-modem-helpers-qmi','test-modem-helpers-mbim'}<=set(selected)
(w/'selected-tests.json').write_text(json.dumps({'selected':selected,'deferred':[t['name'] for t in registered if t['name'] in deferred]},indent=2)+'\n')
with (w/'original-tests.log').open('xb') as log:
 subprocess.run(['meson','test','-C','/build/compile','--no-rebuild','--print-errorlogs',*selected],stdout=log,stderr=subprocess.STDOUT,check=True)
PY
meson install -C /build/compile --destdir /stage --no-rebuild
LD_LIBRARY_PATH=/stage/usr/lib /stage/usr/bin/mmcli --version > /build/actual-version.log 2>&1
python3 - <<'PY'
from pathlib import Path
import hashlib,json,os
w=Path('/build');selection=json.loads((w/'selected-tests.json').read_text())
tests=[json.loads(x) for x in (w/'compile/meson-logs/testlog.json').read_text().splitlines() if x.strip()]
assert len(tests)==len(selection['selected']) and all(t['result']=='OK' and t['returncode']==0 for t in tests)
options={r['name']:r['value'] for r in json.loads((w/'compile/meson-info/intro-buildoptions.json').read_text())}
assert options['polkit']=='strict' and all(options[n] for n in ['mbim','qmi','introspection','udev','systemd_suspend_resume','systemd_journal']) and not options['qrtr']
assert not options['at_command_via_dbus'] and all(r['value']=='auto' for r in json.loads((w/'compile/meson-info/intro-buildoptions.json').read_text()) if r['name'].startswith('plugin_'))
version=(w/'actual-version.log').read_text();assert '1.24.2' in version
assert Path('/stage/usr/lib/pkgconfig/mm-glib.pc').is_file()
r={'scope':'Frozen ModemManager1.24.2 default plugins, MBIM/QMI/GI/Udev/Systemd/strict-polkit build and selected original local parser/data tests. Serial PTY and session stub tests deferred, not passes. No daemon/modem/cellular/firmware/Settings GUI/hardware acceptance.','compile_exit':0,'stage_exit':0,'original_tests':tests,'test_selection':selection,'consumer':{'version':version,'polkit':'strict'},'artifacts':{str(p.relative_to(w/'compile')):hashlib.sha256(p.read_bytes()).hexdigest() for p in (w/'compile').rglob('*') if p.is_file() and not p.is_symlink() and p.open('rb').read(4)==b'\x7fELF'},'stage_sha256':{str(p.relative_to('/stage')):hashlib.sha256(p.read_bytes()).hexdigest() for p in Path('/stage').rglob('*') if p.is_file() and not p.is_symlink()}}
(w/'stage-results.json').write_text(json.dumps(r,indent=2)+'\n');s=os.statvfs('/build');assert s.f_bavail*s.f_frsize>=512*1024**2
PY
