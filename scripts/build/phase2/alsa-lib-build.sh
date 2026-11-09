#!/bin/bash
set -euo pipefail
[[ $(id -u) == 101 && ! -e /build/compile ]]
mkdir /build/compile
cd /build/compile
/src/configure --prefix=/usr --libdir=/usr/lib --disable-static \
    > /build/configure.log 2>&1
make -j4 > /build/compile.log 2>&1
make -j4 check > /build/upstream-tests.log 2>&1
make DESTDIR=/stage install > /build/stage.log 2>&1
cc -std=c11 -Wall -Wextra -Werror /src/toddy-probe.c -I/stage/usr/include \
    -L/stage/usr/lib -Wl,-rpath,/stage/usr/lib -lasound -o /build/consumer
ALSA_PLUGIN_DIR=/stage/usr/lib/alsa-lib /build/consumer > /build/consumer.log 2>&1
python3 - <<'PY'
from pathlib import Path
import json
Path('/build/test-results.json').write_text(json.dumps({
    'scope':'Native ALSA configuration and null PCM API; no audible/physical or Pipewire/GNOME acceptance',
    'upstream_check_exit':0,'upstream_check_scope':'Builds original manual/hardware examples; no automated case count claimed',
    'staged_consumer_exit':0,'profile':'Shared libasound/topology and default source configuration; no user preference edits'
},indent=2)+'\n')
PY
