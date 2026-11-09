#!/bin/bash
set -euo pipefail
[[ $(id -u) == 101 && ! -e /build/compile ]]
mkdir /build/compile
cd /build/compile
/src/configure --prefix=/usr --libdir=/usr/lib --disable-static --disable-external-libs --disable-mpeg --disable-sqlite --enable-alsa > /build/configure.log 2>&1
make -j4 > /build/compile.log 2>&1
make -j4 check > /build/upstream-tests.log 2>&1
make DESTDIR=/stage install > /build/stage.log 2>&1
cc -Wall -Wextra -Werror /src/toddy-probe.c -I/stage/usr/include \
    -L/stage/usr/lib -Wl,-rpath,/stage/usr/lib -lsndfile -o /build/consumer
/build/consumer > /build/consumer.log 2>&1
python3 - <<'PY'
from pathlib import Path
import json
w=Path('/build');results=[]
for path in sorted((w/'compile').rglob('*.trs')):
    text=path.read_text();assert ':test-result: PASS' in text or ':test-result: SKIP' in text,(str(path),text)
    results.append({'name':str(path.relative_to(w/'compile')),'result':'SKIP' if ':test-result: SKIP' in text else 'PASS'})
assert results
(w/'test-results.json').write_text(json.dumps({'scope':'Native provided audio-file tests and exact PCM WAV/refusal API; no device output','upstream_drivers':results,'staged_consumer_exit':0,'profile':'PCM/internal codecs plus ALSA file-player; optional FLAC/Opus/MP3 external codec dependencies omitted'},indent=2)+'\n')
PY
