#!/bin/bash
set -euo pipefail
[[ $(id -u) == 101 && ! -e /build/compile ]]
export PYTHONDONTWRITEBYTECODE=1
ulimit -c 0
meson setup /build/compile /src --prefix=/usr --libdir=lib --buildtype=release --wrap-mode=nofallback -Dbash_completion=false -Dman=false -Dqrtr=false -Dcollection=full -Dmbim_qmux=true -Dintrospection=true -Dfuzzer=false
ninja -C /build/compile -j4 > /build/original-build.log 2>&1
meson introspect /build/compile --tests > /build/original-registered-tests.json
meson test -C /build/compile --no-rebuild --print-errorlogs > /build/original-tests.log 2>&1
meson install -C /build/compile --destdir /stage --no-rebuild
LD_LIBRARY_PATH=/stage/usr/lib /stage/usr/bin/qmicli --version > /build/actual-version.log 2>&1
python3 - <<'PY'
from pathlib import Path
import hashlib,json,os
w=Path('/build');tests=[json.loads(x) for x in (w/'compile/meson-logs/testlog.json').read_text().splitlines() if x.strip()];registered=json.loads((w/'original-registered-tests.json').read_text())
assert tests and len(tests)==len(registered) and all(t['result']=='OK' and t['returncode']==0 for t in tests)
version=(w/'actual-version.log').read_text();assert '1.38.0' in version
config=(w/'compile/config.h').read_text();assert '#undef QMI_USERNAME_ENABLED' in config and '#undef QMI_GROUPNAME_ENABLED' in config
assert Path('/stage/usr/lib/pkgconfig/qmi-glib.pc').is_file()
r={'scope':'Frozen libqmi1.38.0 full message collection/MBIM-QMUX/GI/proxy/CLI/firmware utility compiled with root-only device defaults, all registered original local tests. Book-supported QRTR=false, optional fuzzer/man/docs/completion omitted. No firmware operation/device/proxy-service/cellular network/Settings/physical acceptance.','compile_exit':0,'stage_exit':0,'original_tests':tests,'registered_tests':registered,'consumer':{'version':version,'root_only_device_authorization':True},'artifacts':{str(p.relative_to(w/'compile')):hashlib.sha256(p.read_bytes()).hexdigest() for p in (w/'compile').rglob('*') if p.is_file() and not p.is_symlink() and p.open('rb').read(4)==b'\x7fELF'},'stage_sha256':{str(p.relative_to('/stage')):hashlib.sha256(p.read_bytes()).hexdigest() for p in Path('/stage').rglob('*') if p.is_file() and not p.is_symlink()}}
(w/'stage-results.json').write_text(json.dumps(r,indent=2)+'\n');s=os.statvfs('/build');assert s.f_bavail*s.f_frsize>=512*1024**2
PY
