#!/bin/bash
set -euo pipefail
[[ $(id -u) == 101 && ! -e /build/compile ]]
mkdir /build/compile
cd /build/compile
CFLAGS='-O2 -std=gnu17' /src/configure --prefix=/usr --libdir=/usr/lib --disable-static \
    --disable-oss --disable-gtk --disable-gtk3 --disable-gstreamer --disable-tdb \
    --enable-alsa --enable-pulse --enable-null --disable-lynx \
    > /build/configure.log 2>&1
make -j4 > /build/compile.log 2>&1
make DESTDIR=/stage docdir=/usr/share/doc/libcanberra-0.30 install > /build/stage.log 2>&1
cc -Wall -Wextra -Werror /src/toddy-probe.c -I/stage/usr/include \
    -L/stage/usr/lib -Wl,-rpath,/stage/usr/lib -lcanberra -o /build/consumer
/build/consumer > /build/consumer.log 2>&1
python3 - <<'PY'
from pathlib import Path
import json
w=Path('/build')
for name in ['alsa','pulse','null']:
    assert (w/('stage/usr/lib/libcanberra-0.30/libcanberra-'+name+'.so')).is_file()
(w/'test-results.json').write_text(json.dumps({'scope':'Native Canberra core properties/lifecycle/disabled-event refusal and staged modules; no actual audible output','registered_upstream_suites':0,'upstream_note':'Package has no automated suite per frozen BLFS; interactive example is not a pass','staged_consumer_exit':0,'profile':'Shared core with ALSA/Pulse/null modules; GTK2/GTK3 bindings omitted: selected GNOME50 consumers use core libcanberra, not legacy X11-only binding source. Frozen Wayland patch retained/applied, C GNU17 compatibility profile; no GTK4 extension invented'},indent=2)+'\n')
PY
