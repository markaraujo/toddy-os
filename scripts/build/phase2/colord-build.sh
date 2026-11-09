#!/bin/bash
set -euo pipefail
[[ $(id -u) == 101 && ! -e /build/compile ]]
meson setup /build/compile /src --prefix=/usr --libdir=lib --sysconfdir=/etc --localstatedir=/var --buildtype=release \
    --wrap-mode=nofallback -Ddaemon=false -Dvapi=false -Dsystemd=false -Dudev_rules=false \
    -Dargyllcms_sensor=false -Dbash_completion=false -Ddocs=false -Dman=false \
    -Dtests=true -Dinstalled_tests=false -Dintrospection=true \
    > /build/configure.log 2>&1
ninja -C /build/compile -j4 > /build/compile.log 2>&1
meson test -C /build/compile --no-rebuild --print-errorlogs colord-test-private > /build/upstream-tests.log 2>&1
DESTDIR=/stage meson install -C /build/compile --no-rebuild > /build/stage.log 2>&1
rmdir /stage/var/lib/colord/icc /stage/var/lib/colord /stage/var/lib /stage/var
cc -Wall -Wextra -Werror /src/toddy-probe.c -I/stage/usr/include/colord-1 \
    -L/stage/usr/lib -Wl,-rpath,/stage/usr/lib \
    $(PKG_CONFIG_PATH=/stage/usr/lib/pkgconfig pkg-config --cflags --libs colord gio-2.0 lcms2) -o /build/consumer
LD_LIBRARY_PATH=/stage/usr/lib /build/consumer > /build/consumer.log 2>&1
python3 - <<'PY'
from pathlib import Path
import json,re
w=Path('/build');rows=[json.loads(s) for s in (w/'compile/meson-logs/testlog.json').read_text().splitlines() if s.strip()]
assert len(rows)==1 and rows[0]['result']=='OK' and rows[0]['returncode']==0
cases=re.findall(r'^ok [0-9]+ .*$',rows[0].get('stdout',''),re.M);skips=[s for s in cases if '# SKIP' in s]
assert cases and not skips
assert not (w/'stage/usr/libexec/colord').exists()
(w/'test-results.json').write_text(json.dumps({'scope':'Native Colord client/ICC/data libraries and original private data cases; no system color service/physical sensor acceptance','original_private_driver_exit':0,'original_private_cases':len(cases),'staged_consumer_exit':0,'profile':'Supported daemon=false bootstrap for Mutter client dependency; no colord user, service, policy, udev rules or mutable state directories. Full daemon/polkit/color-device integration remains unqualified; no service pass inferred.','omitted':'Daemon and physical colorhug tests not selected'},indent=2)+'\n')
PY
