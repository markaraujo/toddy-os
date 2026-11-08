#!/bin/bash
# Frozen BLFS13.1 Sassc3.6.2 against independently qualified native LibSass3.6.6.
set -euo pipefail
[[ $(id -u) == 101 && -f /src/configure.ac && -d /stage ]]
cp -a /src /build/compile
cd /build/compile
export SASSC_VERSION=3.6.2
autoreconf -fi
CFLAGS='-O2 -g0' CXXFLAGS='-O2 -g0' ./configure --prefix=/usr --with-libsass=/usr
make -j4
make DESTDIR=/stage install
PATH=/stage/usr/bin:$PATH python3 -B /src/toddy-probe.py > /build/consumer.json
python3 - <<'PY'
import json
from pathlib import Path
proof=json.loads(Path('/build/consumer.json').read_text());assert len(proof['checks'])==4
Path('/build/test-results.json').write_text(json.dumps({'scope':'Native stylesheet build wrapper; no graphical or catalog acceptance',
    'registered_upstream_suite':'Not bundled; frozen BLFS13.1 states no test suite, external Ruby Sass-spec not claimed passed',
    'staged_consumer_exit':0,'consumer':proof,
    'version_source':'Supported upstream SASSC_VERSION=3.6.2 override for authenticated archive without VCS metadata'},indent=2)+'\n')
PY
