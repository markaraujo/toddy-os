#!/bin/bash
# Native seccomp library; full original C regressions and real child-only filter.
set -euo pipefail
[[ $(id -u) == 101 && -f /src/configure && -d /stage ]]
mkdir /build/compile
cd /build/compile
/src/configure --prefix=/usr --libdir=/usr/lib --disable-python --disable-static
make -j4
make -j4 check > /build/upstream-check.log 2>&1
(cd tests && bash /src/tests/regression -T live -m c -j 2) > /build/upstream-live.log 2>&1
make DESTDIR=/stage install
export PKG_CONFIG_PATH=/stage/usr/lib/pkgconfig
cc -std=c11 -D_GNU_SOURCE -Wall -Wextra -Werror /src/toddy-probe.c \
    -I/stage/usr/include -L/stage/usr/lib -Wl,-rpath,/stage/usr/lib \
    $(pkg-config --cflags --libs libseccomp) -o /build/native-filter
/build/native-filter > /build/native-filter.log 2>&1
python3 - <<'PY'
from pathlib import Path
import json
import re
def summary(path):
    text=Path(path).read_text()
    rows={k:int(v) for k,v in re.findall(r'^ tests (run|skipped|passed|failed|errored): (\d+)$',text,re.M)}
    assert rows['run']==rows['passed']>0 and rows['failed']==rows['errored']==0
    return rows
Path('/build/test-results.json').write_text(json.dumps({'scope':'Native seccomp C/default and actual kernel live regressions; child-only syscall refusal/parent unaffected, not global policy or full application sandbox acceptance',
'original_summary':summary('/build/upstream-check.log'),'live_summary':summary('/build/upstream-live.log'),
'upstream_exit':0,'staged_consumer_exit':0,'child_syscall_denied':True,'parent_unaffected':True,'malformed_action_refused':True,
'profile':'Shared C library/tools; optional Python binding disabled. Valgrind/incompatible architecture skips are not counted as passes.'},indent=2)+'\n')
PY
