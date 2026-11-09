#!/bin/bash
# Frozen Linux-PAM1.7.2 plus ADR0126 backports; no guest login writes.
set -euo pipefail
[[ $(id -u) == 101 && -f /src/meson.build && -d /stage ]]
[[ -r /etc/pam.d/other && ! -w /etc/pam.d/other ]]
meson setup /build/compile /src --prefix=/usr --libdir=lib --sysconfdir=/etc \
    --localstatedir=/var --buildtype=release --wrap-mode=nofallback \
    -Ddocs=disabled -Dlogind=enabled -Dnis=disabled -Dselinux=disabled \
    -Daudit=disabled -Deconf=disabled -Dpam_userdb=disabled
ninja -C /build/compile -j4
meson test -C /build/compile --no-rebuild --print-errorlogs -j2 \
    > /build/original-tests.log 2>&1
printf '0\n' > /build/original-tests.exit
DESTDIR=/stage ninja -C /build/compile install
cc -Wall -Wextra -Werror /src/toddy-probe.c -I/stage/usr/include \
    -L/stage/usr/lib -Wl,-rpath,/stage/usr/lib -lpam -o /build/native-consumer
/build/native-consumer /build/consumer-policy /stage/usr/lib/security \
    > /build/native-consumer.log 2>&1
python3 - <<'PY'
from pathlib import Path
import json
rows=[json.loads(s) for s in Path('/build/compile/meson-logs/testlog.json').read_text().splitlines() if s.strip()]
assert rows and all(r['result']=='OK' and r['returncode']==0 for r in rows)
proof={'scope':'Original unprivileged native PAM unit drivers and actual staged API/module allow-deny/malformed/refusal recovery; real passwords/privileged helper/login/session still pending',
       'build_exit':0,'stage_exit':0,'consumer_exit':0,'original_tests':[{k:r[k] for k in ['name','result','returncode']} for r in rows],
       'unqualified':'Optional pam_userdb/NIS/SELinux/audit/libeconf disabled; privileged xtests and real shadow password/helper/session/boot not yet run'}
Path('/build/stage-results.json').write_text(json.dumps(proof,indent=2)+'\n')
PY
