#!/bin/bash
set -euo pipefail
[[ $(id -u) == 101 && ! -e /build/compile ]]
ulimit -c 0
cmake -S /src -B /build/compile -G Ninja -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_PREFIX=/usr \
    -DCMAKE_INSTALL_LIBDIR=lib -DCMAKE_SKIP_INSTALL_RPATH=ON -DBUILD_SHARED_LIBS=ON -Dtiff-static=OFF \
    -Dtiff-tests=ON -Dtiff-tools=ON -Dtiff-contrib=OFF -Dtiff-docs=OFF -Dsphinx=OFF -Dtiff-opengl=OFF \
    -Djpeg=ON -Dzlib=ON -Dlzma=ON -Dzstd=ON -Dwebp=OFF -Dlerc=OFF -Djbig=OFF -Dlibdeflate=OFF
cmake --build /build/compile -j4
ctest --test-dir /build/compile --output-on-failure --parallel 4 --output-junit /build/ctest.xml
DESTDIR=/stage cmake --install /build/compile
cc -std=c11 -D_GNU_SOURCE -Wall -Wextra -Werror /src/toddy-probe.c -I/stage/usr/include \
    -L/stage/usr/lib $(PKG_CONFIG_PATH=/stage/usr/lib/pkgconfig pkg-config --cflags --libs libtiff-4) -o /build/tiff-consumer
LD_LIBRARY_PATH=/stage/usr/lib /build/tiff-consumer > /build/native-image.log 2>&1
python3 - <<'PY'
from pathlib import Path
import json,xml.etree.ElementTree as ET
root=ET.parse('/build/ctest.xml').getroot();rows=root.findall('.//testcase')
assert rows and all(r.find('failure') is None and r.find('skipped') is None for r in rows)
Path('/build/test-results.json').write_text(json.dumps({'scope':'Actual native TIFF upstream tests and compressed image roundtrip/invalid input refusal; no graphical session',
    'registered_tests':len(rows),'upstream_exit':0,'staged_consumer_exit':0,
    'native_image_stdout':Path('/build/native-image.log').read_text()},indent=2)+'\n')
PY
