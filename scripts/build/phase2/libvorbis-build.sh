#!/bin/bash
set -euo pipefail
[[ $(id -u) == 101 && ! -e /build/compile ]]
mkdir /build/compile
cd /build/compile
/src/configure --prefix=/usr --libdir=/usr/lib --disable-static --disable-docs > /build/configure.log 2>&1
make -j4 > /build/compile.log 2>&1
make -j1 check > /build/upstream-tests.log 2>&1
make DESTDIR=/stage install > /build/stage.log 2>&1
cc -Wall -Wextra -Werror /src/toddy-probe.c -I/stage/usr/include \
    -L/stage/usr/lib -Wl,-rpath,/stage/usr/lib -lvorbisenc -lvorbisfile -lvorbis -logg -o /build/consumer
/build/consumer > /build/consumer.log 2>&1
python3 - <<'PY'
from pathlib import Path
import json
w=Path('/build');text=(w/'upstream-tests.log').read_text()
cases=sum(1 for line in text.splitlines() if 'vorbis_' in line and line.rstrip().endswith(' : ok'))
assert cases==528,cases
(w/'test-results.json').write_text(json.dumps({'scope':'Original Vorbis codec write/read suite and native C header/metadata/refusal APIs; no audible or desktop acceptance','upstream_exit':0,'upstream_codec_roundtrips':cases,'staged_consumer_exit':0},indent=2)+'\n')
PY
