#!/bin/bash
set -euo pipefail
[[ $(id -u) == 101 && ! -e /build/compile ]]
export PYTHONDONTWRITEBYTECODE=1
meson setup /build/compile /src --prefix=/usr --libdir=lib --libexecdir=libexec \
    --sysconfdir=/etc --localstatedir=/var --buildtype=release --wrap-mode=nodownload \
    -Dlibcap-ng=disabled -Dselinux=disabled -Dssh-agent=false -Dsystemd=enabled \
    -Dpam=true -Ddebug-mode=false -Dmanpage=false
ninja -C /build/compile -j4
# These five original tests require WITH_DEBUG-only fixture service/login hooks.
# Keep production hooks disabled and test that distinct profile separately.
python3 - <<'PYTEST'
from pathlib import Path
import json,subprocess
p=Path('/build');rows=json.loads((p/'compile/meson-info/intro-tests.json').read_text())
fixture={'dbus-search','dbus-items','dbus-signals','dbus-lock','dbus-portal'}
assert len(rows)==62 and {r['name'] for r in rows if any(s.endswith(':gkr-daemon-dbus') for s in r.get('suite',[]))}==fixture
with (p/'original-tests.log').open('x') as log:
 r=subprocess.run(['meson','test','-C','/build/compile','--no-rebuild','--print-errorlogs','-j2','--no-suite','gkr-daemon-dbus'],stdout=log,stderr=subprocess.STDOUT)
(p/'production-original-tests.exit').write_text(str(r.returncode)+'\n');assert r.returncode==0
PYTEST
python3 /src/toddy-fixtures.py
python3 /src/toddy-finish.py "$(cat /src/toddy-probe.py)"
dbus-run-session -- python3 /src/toddy-backend.py /stage /build/production-backend-4.json
