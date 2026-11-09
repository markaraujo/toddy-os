#!/bin/bash
set -euo pipefail
[[ $(id -u) == 101 && ! -e /build/compile && -d /src/toddy-test-sdk ]]
ln -s /src/toddy-test-sdk /build/test-sdk
export PKG_CONFIG_PATH=/build/test-sdk/lib/pkgconfig
export LD_LIBRARY_PATH=/build/test-sdk/lib
meson setup /build/compile /src --prefix=/usr --libdir=lib --buildtype=release \
    --default-library=both --wrap-mode=nofallback -Dtests=enabled -Dtools=enabled -Ddocumentation=disabled \
    > /build/configure.log 2>&1
ninja -C /build/compile -j4 > /build/compile.log 2>&1
meson test -C /build/compile --no-rebuild --print-errorlogs > /build/upstream-tests.log 2>&1
DESTDIR=/stage meson install -C /build/compile --no-rebuild > /build/stage.log 2>&1
cc -std=c11 -Wall -Wextra -Werror /src/toddy-probe.c -I/stage/usr/include/libevdev-1.0 \
    -L/stage/usr/lib -Wl,-rpath,/stage/usr/lib \
    $(PKG_CONFIG_PATH=/stage/usr/lib/pkgconfig pkg-config --cflags --libs libevdev) -o /build/consumer
/build/consumer > /build/consumer.log 2>&1
python3 - <<'PY'
from pathlib import Path
import json,re
rows=[json.loads(s) for s in Path('/build/compile/meson-logs/testlog.json').read_text().splitlines() if s.strip()]
assert len(rows)==6
drivers=[];checks=0
root_cases={'test-internals','test-uinput','test-libevdev','test-kernel'}
for row in rows:
    name=row['name'].split(':')[-1];output=row.get('stdout','')+row.get('stderr','')
    if row['result']=='SKIP':
        assert row['returncode']==77 and name in root_cases and 'needs to run as root' in output
        count=0
    else:
        assert row['result']=='OK' and row['returncode']==0
        summaries=re.findall(r'Checks:\s*(\d+), Failures:\s*(\d+), Errors:\s*(\d+)',output)
        assert all(int(f)==int(e)==0 for _,f,e in summaries)
        count=sum(int(n) for n,_,_ in summaries)
        if name=='test-event-codes':assert count>0
    checks+=count;drivers.append({'name':name,'result':row['result'],'exit':row['returncode'],'check_cases':count})
assert checks>0
Path('/build/test-results.json').write_text(json.dumps({'scope':'Native portable input-code/API qualification only; no uinput/physical/GNOME acceptance',
    'upstream_drivers':drivers,'native_check_cases':checks,'staged_consumer_exit':0,
    'private_sdk':'Reused qualified Check0.15.2 bytes/9oldSDKcases, no rebuild or global install',
    'kernel_device_suites':'Any root/uinput-dependent driver SKIP77 remains explicitly untested'},indent=2)+'\n')
PY
