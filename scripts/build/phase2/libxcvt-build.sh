#!/bin/bash
set -euo pipefail
[[ $(id -u) == 101 && ! -e /build/compile ]]
meson setup /build/compile /src --prefix=/usr --libdir=lib --buildtype=release \
    --wrap-mode=nofallback > /build/configure.log 2>&1
ninja -C /build/compile -j4 > /build/compile.log 2>&1
DESTDIR=/stage meson install -C /build/compile --no-rebuild > /build/stage.log 2>&1
cc -std=c11 -Wall -Wextra -Werror /src/toddy-probe.c -I/stage/usr/include \
    -L/stage/usr/lib -Wl,-rpath,/stage/usr/lib \
    $(PKG_CONFIG_PATH=/stage/usr/lib/pkgconfig pkg-config --cflags --libs libxcvt) -o /build/consumer
/build/consumer > /build/consumer.log 2>&1
LD_LIBRARY_PATH=/stage/usr/lib /stage/usr/bin/cvt 1920 1080 60 > /build/cli.log 2>&1
python3 - <<'PY'
from pathlib import Path
import json
assert json.loads(Path('/build/compile/meson-info/intro-tests.json').read_text())==[]
assert 'Modeline' in Path('/build/cli.log').read_text()
Path('/build/test-results.json').write_text(json.dumps({'scope':'Actual native CVT timing arithmetic/API and CLI only, no physical monitor/mode-setting acceptance',
    'registered_upstream_tests':0,'upstream_suite':'No test suite provided; empty target is not acceptance',
    'staged_consumer_exit':0,'cli_exit':0,'timing_profiles':['1920x1080@60progressive','1920x1080@60reduced-blanking'],
    'invalid_dimensions':'Not exercised outside upstream API preconditions'},indent=2)+'\n')
PY
