#!/bin/bash
# Native unprivileged user-namespace sandbox; no setuid product or global policy.
set -euo pipefail
[[ $(id -u) == 101 && -f /src/meson.build && -d /stage ]]
meson setup /build/compile /src --prefix=/usr --libdir=lib --buildtype=release \
    --wrap-mode=nofallback -Dtests=true -Dsupport_setuid=false -Dselinux=disabled \
    -Dman=disabled -Dbash_completion=disabled -Dzsh_completion=disabled
ninja -C /build/compile -j4
# Shell/namespace drivers require the native Toddy kernel, not this Ubuntu
# compiler environment. The existing boot probe and stage qualifier finish them.
meson test -C /build/compile --no-rebuild --print-errorlogs test-utils
python3 - <<'PYTHON'
from pathlib import Path
import json
rows=[json.loads(x) for x in Path('/build/compile/meson-logs/testlog.json').read_text().splitlines()]
assert len(rows)==1 and rows[0]['result']=='OK' and rows[0]['returncode']==0
Path('/build/build-results.json').write_text(json.dumps({'scope':'Compiled native bwrap only; unqualified until native kernel runtime proof and stage',
'portable_utility_exit':0,'native_runtime_pending':['test-run.sh','test-specifying-pidns.sh','test-specifying-userns.sh','optional test-seccomp.py'],
'package_promotable':False},indent=2)+'\n')
PYTHON
