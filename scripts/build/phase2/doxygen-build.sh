#!/bin/bash
set -euo pipefail
[[ $(id -u) == 101 && ! -e /build/compile ]]
ulimit -c 0
export PYTHONDONTWRITEBYTECODE=1
cmake -S /src -B /build/compile -G Ninja -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_PREFIX=/usr \
    -DCMAKE_INSTALL_LIBDIR=lib -DCMAKE_SKIP_INSTALL_RPATH=ON -Dbuild_doc=OFF -Dbuild_wizard=OFF \
    -Dbuild_search=OFF -Dbuild_app=OFF -Dbuild_parse=OFF -Duse_libclang=OFF -Duse_sys_sqlite3=ON
cmake --build /build/compile -j4
ctest --test-dir /build/compile --output-on-failure --parallel 4 --timeout 180 --output-junit /build/ctest.xml
DESTDIR=/stage cmake --install /build/compile
PATH=/stage/usr/bin:$PATH python3 /src/toddy-probe.py /build/native-consumer > /build/native-consumer.log
python3 - <<'PY'
from pathlib import Path
import json,xml.etree.ElementTree as ET
root=ET.parse('/build/ctest.xml').getroot();rows=root.findall('.//testcase')
assert rows and all(r.find('failure') is None and r.find('error') is None and r.find('skipped') is None for r in rows)
Path('/build/test-results.json').write_text(json.dumps({'scope':'Native build-only Doxygen parser/XML generator, not a required desktop app or catalog candidate',
    'registered_tests':len(rows),'upstream_exit':0,'staged_consumer_exit':0,'consumer':json.loads(Path('/build/native-consumer/results.json').read_text()),
    'profile':'No GUI/docs/search/Clang parser; native system SQLite, authenticated bundled fmt/spdlog'},indent=2)+'\n')
PY
