#!/bin/bash
set -euo pipefail
[[ $(id -u) == 101 && ! -e /build/compile ]]
# Optional Python test SDK is absent. Keep all original registered data/CLI
# drivers and compile the four original C test declarations independently.
meson setup /build/compile /src --prefix=/usr --libdir=lib --sysconfdir=/etc \
    --buildtype=release --wrap-mode=nofallback -Dtests=disabled \
    -Ddocumentation=disabled > /build/configure.log 2>&1
ninja -C /build/compile -j4 > /build/compile.log 2>&1
meson test -C /build/compile --no-rebuild --print-errorlogs > /build/upstream-tests.log 2>&1
DESTDIR=/stage meson install -C /build/compile --no-rebuild > /build/stage.log 2>&1
python3 - <<'PY'
from pathlib import Path
import json,re,shlex,subprocess
work=Path('/build');rows=[]
flags=shlex.split(subprocess.check_output(['pkg-config','--cflags','--libs','glib-2.0'],text=True))
for name in ['test-load','test-dbverify','test-tablet-validity','test-stylus-validity']:
    binary=work/name
    subprocess.run(['cc','-std=gnu99','-DTOPSRCDIR="/src"','-I/src/include','-I/src/libwacom',
                    '-I/build/compile','-I/build/compile/include','/src/test/'+name+'.c',
                    '-L/stage/usr/lib','-Wl,-rpath,/stage/usr/lib',*flags,'-lwacom','-o',str(binary)],check=True)
    with (work/(name+'.log')).open('xb') as log:
        r=subprocess.run([str(binary)],stdout=log,stderr=subprocess.STDOUT,timeout=120)
    (work/(name+'.exit')).write_text(str(r.returncode)+'\n');assert r.returncode==0
    text=(work/(name+'.log')).read_text();cases=re.findall(r'^ok \d+[^\n]*',text,re.M)
    skipped=sum(' # SKIP' in case for case in cases)
    assert len(cases)>skipped and not re.search(r'^not ok ',text,re.M)
    rows.append({'name':name,'exit':0,'passed_cases':len(cases)-skipped,'skipped_cases':skipped})
(work/'original-c-tests.json').write_text(json.dumps(rows,indent=2)+'\n')
PY
cc -Wall -Wextra -Werror /src/toddy-probe.c -I/stage/usr/include/libwacom-1.0 \
    -L/stage/usr/lib -Wl,-rpath,/stage/usr/lib -lwacom -o /build/consumer
/build/consumer /stage/usr/share/libwacom > /build/consumer.log 2>&1
python3 - <<'PY'
from pathlib import Path
import json
work=Path('/build');rows=[json.loads(s) for s in (work/'compile/meson-logs/testlog.json').read_text().splitlines() if s.strip()]
assert rows
for r in rows:
    assert (r['result']=='OK' and r['returncode']==0) or (r['result']=='SKIP' and r['returncode']==77 and r['name'].endswith('files-in-git'))
(work/'test-results.json').write_text(json.dumps({
    'scope':'Native tablet/stylus database and original data/C/CLI tests only; no physical input, installed hwdb event or GNOME tablet settings acceptance',
    'registered_drivers':[{'name':r['name'],'result':r['result'],'exit':r['returncode']} for r in rows],
    'original_c_drivers':json.loads((work/'original-c-tests.json').read_text()),'staged_consumer_exit':0,
    'selection':'Four unchanged original C target sources/include/define declarations compiled directly; optional Python libevdev/pyudev/pytest SDK unavailable, four Python suites omitted/not passes',
    'profile':'Native library/tools/tablet+stylus data/udev rule and hwdb source; no global hwdb activation before native integration check'
},indent=2)+'\n')
PY
