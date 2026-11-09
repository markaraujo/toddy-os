#!/bin/bash
set -euo pipefail
[[ $(id -u) == 101 && ! -e /build/compile && -f /src/subprojects/munit/meson.build ]]
meson setup /build/compile /src --prefix=/usr --libdir=lib --buildtype=release \
    --wrap-mode=nodownload -Dtests=auto -Ddocumentation=[] -Dlibei=enabled -Dlibeis=enabled \
    -Dliboeffis=enabled -Dsd-bus-provider=libsystemd > /build/configure.log 2>&1
ninja -C /build/compile -j4 > /build/compile.log 2>&1
# Select the original C suites explicitly; optional Python/format/provider
# matrices do not become mandatory because another tool happens to be present.
meson test -C /build/compile --no-rebuild --print-errorlogs \
    unit-tests-utils unit-tests-ei unit-tests-eis unit-tests-oeffis \
    eierpecken eierpecken-no-sigalrm > /build/upstream-tests.log 2>&1
# Upstream Munit sets install=true as a subproject; it is a test dependency.
DESTDIR=/stage meson install -C /build/compile --no-rebuild --skip-subprojects=munit > /build/stage.log 2>&1
cc -std=c11 -Wall -Wextra -Werror /src/toddy-probe.c \
    -I/stage/usr/include/libei-1.0 -I/stage/usr/include/libeis-1.0 -I/stage/usr/include/liboeffis-1.0 \
    -L/stage/usr/lib -Wl,-rpath,/stage/usr/lib \
    $(PKG_CONFIG_PATH=/stage/usr/lib/pkgconfig pkg-config --cflags --libs libei-1.0 libeis-1.0 liboeffis-1.0) \
    -o /build/consumer
/build/consumer > /build/consumer.log 2>&1
python3 - <<'PY'
from pathlib import Path
import json,re
selected={'unit-tests-utils','unit-tests-ei','unit-tests-eis','unit-tests-oeffis','eierpecken','eierpecken-no-sigalrm'}
rows=[json.loads(s) for s in Path('/build/compile/meson-logs/testlog.json').read_text().splitlines() if s.strip()]
assert len(rows)==6 and {r['name'].split(':')[-1] for r in rows}==selected
results=[]
for r in rows:
    assert r['result']=='OK' and r['returncode']==0
    text=r.get('stdout','')+r.get('stderr','')
    summaries=re.findall(r'(\d+) of (\d+) \(\d+%\) tests successful, (\d+) \(\d+%\) test skipped',text)
    assert summaries and all(int(p)==int(total) for p,total,_ in summaries)
    count=sum(int(p) for p,_,_ in summaries)
    skipped=sum(int(s) for _,_,s in summaries)
    results.append({'name':r['name'],'exit':r['returncode'],'case_executions':count,'skipped_cases':skipped})
assert sum(r['case_executions'] for r in results)>0
assert not any('munit' in str(p.relative_to('/stage')) for p in Path('/stage').rglob('*'))
registered=json.loads(Path('/build/compile/meson-info/intro-tests.json').read_text())
Path('/build/test-results.json').write_text(json.dumps({'scope':'Native selected original C EI/EIS/Oeffis and in-process protocol tests plus context/FD consumer; no actual desktop portal or physical input acceptance',
    'upstream_selected':results,'staged_consumer_exit':0,'test_dependency_installed':False,
    'registered_not_selected':[r['name'] for r in registered if r['name'] not in selected],
    'counting':'C driver case executions; signal/no-signal drivers reuse cases in distinct original upstream modes, not unique-case count'},indent=2)+'\n')
PY
