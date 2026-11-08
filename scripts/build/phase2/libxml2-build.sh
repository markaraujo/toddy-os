#!/bin/bash
# BLFS13.1 libxml2-2.15.3; selected core for Wayland/GNOME, not optional bindings.
set -euo pipefail
[[ $(id -u) == 101 && -f /src/meson.build && -d /stage ]]
meson setup /build/compile /src --prefix=/usr --libdir=lib --buildtype=release \
    --wrap-mode=nofallback -Ddocs=disabled -Dpython=disabled -Dicu=disabled \
    -Dhistory=disabled -Dhttp=disabled -Dlegacy=disabled
ninja -C /build/compile -j4
mkdir -p /build/testdata /build/test-output /build/test-logs
# Upstream registers source cwd; run unmodified binaries from private cwd with
# read-only fixture links so output/logs never require a writable source tree.
for path in /src/*;do ln -s "$path" "/build/testdata/$(basename "$path")";done
cd /build/testdata
python3 - <<'TEST'
import json,subprocess,time
from pathlib import Path
results=[]
for name in ['testdict','testchar','testparser','testrecurse','testcatalog','testapi','runtest']:
    command=['/build/compile/'+name]
    if name=='runtest':command+=['--out','/build/test-output/']
    started=time.monotonic()
    with open('/build/test-logs/'+name+'.log','xb') as log:
        result=subprocess.run(command,stdout=log,stderr=subprocess.STDOUT)
    results.append({'name':name,'exit':result.returncode,'seconds':round(time.monotonic()-started,3)})
    Path('/build/test-results.json').write_text(json.dumps(results,indent=2)+'\n')
    if result.returncode:raise SystemExit(result.returncode)
TEST
DESTDIR=/stage ninja -C /build/compile install
[[ -f /stage/usr/bin/xmllint && -f /stage/usr/lib/pkgconfig/libxml-2.0.pc ]]
