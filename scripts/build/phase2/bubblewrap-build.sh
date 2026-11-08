#!/bin/bash
# Native unprivileged user-namespace sandbox; no setuid product or global policy.
set -euo pipefail
[[ $(id -u) == 101 && -f /src/meson.build && -d /stage ]]
meson setup /build/compile /src --prefix=/usr --libdir=lib --buildtype=release \
    --wrap-mode=nofallback -Dtests=true -Dsupport_setuid=false -Dselinux=disabled \
    -Dman=disabled -Dbash_completion=disabled -Dzsh_completion=disabled
ninja -C /build/compile -j4
meson test -C /build/compile --no-rebuild --print-errorlogs
DESTDIR=/stage ninja -C /build/compile install
python3 -B /src/toddy-probe.py /stage/usr/bin/bwrap > /build/native-namespace.log 2>&1
python3 - <<'PY'
from pathlib import Path
import json
rows=[json.loads(x) for x in Path('/build/compile/meson-logs/testlog.json').read_text().splitlines()]
assert len(rows)==5 and all(r['result'] in ['OK','SKIP'] and r['returncode']==0 and not r['is_fail'] for r in rows)
assert any(r['name'].split(':')[-1]=='test-run.sh' and r['result']=='OK' for r in rows)
Path('/build/test-results.json').write_text(json.dumps({'scope':'Native unprivileged user-namespace sandbox core; not complete Glycin sandbox or installed OS acceptance',
'upstream_drivers':[{'name':r['name'],'native_exit':r['returncode'],'result':r['result'],'stdout':r.get('stdout','')} for r in rows],
'staged_consumer_exit':0,'profile':'Setuid support disabled; unprivileged user/mount/PID/network namespaces, no global host/security change. Optional Python seccomp-binding driver may be unavailable and is never counted as a pass.'},indent=2)+'\n')
PY
