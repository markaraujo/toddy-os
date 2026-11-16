#!/bin/bash
set -euo pipefail
[[ $(id -u) == 101 && ! -e /build/compile ]]
# Run only in the qualified unprivileged read-only /src, private /build,/stage
# no-network build harness. Preparation removed the unconditional Sonic fetch.
cmake -S /src -B /build/compile -DCMAKE_INSTALL_PREFIX=/usr \
    -DCMAKE_INSTALL_LIBDIR=lib -DCMAKE_BUILD_TYPE=Release \
    -DFETCHCONTENT_FULLY_DISCONNECTED=ON -DBUILD_SHARED_LIBS=OFF \
    -DUSE_LIBSONIC=OFF -DUSE_LIBPCAUDIO=OFF -DUSE_MBROLA=OFF \
    -DESPEAK_COMPAT=OFF -DUSE_ASYNC=OFF \
    > /build/configure.log 2>&1
cmake --build /build/compile -j4 > /build/compile.log 2>&1
cmake --build /build/compile --target tests -j4 > /build/tests-build.log 2>&1
ctest --test-dir /build/compile --output-on-failure --timeout 60 \
    > /build/upstream-tests.log 2>&1
DESTDIR=/stage cmake --install /build/compile > /build/stage.log 2>&1
# Explicit file-only synthesis; no sound output backend is built or opened.
for language in en-us pt-br; do
    ESPEAK_DATA_PATH=/stage/usr/share /stage/usr/bin/espeak-ng \
        -v "$language" -w "/build/$language.wav" 'Toddy system test.' \
        > "/build/$language.log" 2>&1
done
python3 - <<'CHECK'
from pathlib import Path
import json,wave
for language in ('en-us','pt-br'):
    with wave.open('/build/'+language+'.wav') as stream:
        assert stream.getnchannels()==1 and stream.getsampwidth()==2
        assert 0<stream.getnframes()<=stream.getframerate()*30
Path('/build/test-results.json').write_text(json.dumps({
    'scope':'Original CTest exit plus built-in EN/PT WAV generation only; no intelligibility/device acceptance',
    'upstream_ctest_exit':0,'file_only_synthesis_exit':0,
    'playback_backend':False,'neural_voice':False},indent=2)+'\n')
CHECK
install -Dm644 /src/COPYING /stage/usr/share/doc/espeak-ng/COPYING
