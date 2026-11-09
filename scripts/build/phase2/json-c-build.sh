#!/bin/bash
# Frozen shared-library profile, no hardware RNG; build-only upstream parser test application.
set -euo pipefail
[[ $(id -u) == 101 ]]
cmake -S /src -B /build/compile -G Ninja -DCMAKE_INSTALL_PREFIX=/usr \
    -DCMAKE_INSTALL_LIBDIR=lib -DCMAKE_BUILD_TYPE=Release -DBUILD_STATIC_LIBS=OFF \
    -DBUILD_SHARED_LIBS=ON -DBUILD_TESTING=ON -DBUILD_APPS=ON \
    -DENABLE_THREADING=ON -DENABLE_RDRAND=OFF -DDISABLE_EXTRA_LIBS=ON
cmake --build /build/compile -j4
USE_VALGRIND=0 ctest --test-dir /build/compile --output-on-failure -j4 > /build/original-tests.log 2>&1
DESTDIR=/stage cmake --install /build/compile
export PKG_CONFIG_LIBDIR=/stage/usr/lib/pkgconfig:/usr/lib/pkgconfig:/usr/share/pkgconfig
cc -Wall -Wextra -Werror /src/toddy-probe.c -I/stage/usr/include -L/stage/usr/lib \
    -Wl,-rpath,/stage/usr/lib -ljson-c -o /build/consumer
/build/consumer > /build/native-consumer.json
python3 - <<'PY'
from pathlib import Path
import hashlib,json,xml.etree.ElementTree as ET
p=Path('/build');xml=list((p/'compile/Testing').glob('*/Test.xml'))
# CTest's normal text summary and authoritative registered test inventory.
text=(p/'original-tests.log').read_text();assert '100% tests passed' in text
import re,subprocess
m=re.search(r'out of (\d+)',text);assert m and int(m.group(1))>10
registered=json.loads(subprocess.check_output(['ctest','--test-dir',str(p/'compile'),'--show-only=json-v1'],text=True))['tests'];assert len(registered)==int(m.group(1))
(p/'stage-results.json').write_text(json.dumps({'scope':'Original JSON-C shared-library tests plus actual strict typed/UTF8/depth/refusal/recovery C consumer; no AccountsService/GNOME runtime acceptance','compile_exit':0,'stage_exit':0,'original_programs':len(registered),'original_tests_exit':0,'consumer':json.loads((p/'native-consumer.json').read_text()),'profile':'Partial atomic reference counting enabled, not general object thread safety; hardware RDRAND/extra libraries/static library disabled; upstream build-only app not installed','stage_sha256':{str(f.relative_to(p/'stage')):hashlib.sha256(f.read_bytes()).hexdigest() for f in (p/'stage').rglob('*') if f.is_file() and not f.is_symlink()}},indent=2)+'\n')
PY
