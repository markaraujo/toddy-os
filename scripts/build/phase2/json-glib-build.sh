#!/bin/bash
set -euo pipefail
[[ $(id -u) == 101 && ! -e /build/compile ]]
export PYTHONDONTWRITEBYTECODE=1
meson setup /build/compile /src --prefix=/usr --libdir=lib --buildtype=release \
    --wrap-mode=nofallback -Dintrospection=enabled -Ddocumentation=disabled \
    -Dman=false -Dtests=true -Dconformance=true -Dinstalled_tests=false -Dnls=enabled \
    > /build/configure.log 2>&1
ninja -C /build/compile -j4 > /build/compile.log 2>&1
meson test -C /build/compile --no-rebuild --print-errorlogs > /build/upstream-tests.log 2>&1
DESTDIR=/stage meson install -C /build/compile --no-rebuild > /build/stage.log 2>&1
cc -Wall -Wextra -Werror /src/toddy-probe.c -I/stage/usr/include/json-glib-1.0 \
    -L/stage/usr/lib -Wl,-rpath,/stage/usr/lib \
    $(pkg-config --cflags --libs gio-2.0) -ljson-glib-1.0 -o /build/consumer
/build/consumer > /build/consumer.log 2>&1
GI_TYPELIB_PATH=/stage/usr/lib/girepository-1.0 LD_LIBRARY_PATH=/stage/usr/lib python3 - <<'PY' > /build/gi.log 2>&1
import gi
gi.require_version('Json','1.0')
from gi.repository import Json
parser=Json.Parser.new()
assert parser.load_from_data('{"name":"Toddy ação","count":42}',-1)
obj=parser.get_root().get_object()
assert obj.get_string_member('name')=='Toddy ação' and obj.get_int_member('count')==42
print('Native Json1.0 GIR/typelib and Unicode/object/integer parse')
PY
python3 - <<'PY'
from pathlib import Path
import json,re
w=Path('/build');rows=[json.loads(s) for s in (w/'compile/meson-logs/testlog.json').read_text().splitlines() if s.strip()]
assert len(rows)==17 and all(r['result']=='OK' and r['returncode']==0 for r in rows)
drivers=[]
for r in rows:
    text=r.get('stdout','')+r.get('stderr','')
    cases=re.findall(r'^ok\s+\d+[^\n]*',text,re.M)
    skipped=sum(' # SKIP' in line for line in cases)
    drivers.append({'name':r['name'],'exit':r['returncode'],'passed_cases':len(cases)-skipped,'skipped_cases':skipped})
(w/'test-results.json').write_text(json.dumps({
    'scope':'Native JSON-GLib original unit/conformance and C/GI parser APIs only; no desktop/network/service acceptance',
    'upstream_drivers':drivers,'staged_consumer_exit':0,'gi_exit':0,
    'profile':'Shared library/tools/GI/translations, full provided conformance corpus; docs/manual/installed test executables omitted',
    'counting':'Actual TAP case executions; intentional error-refusal fixtures are passes only after original assertions. Skips listed separately.'
},indent=2)+'\n')
PY
