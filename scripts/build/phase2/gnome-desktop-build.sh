#!/bin/bash
set -euo pipefail
[[ $(id -u) == 101 && ! -e /build/compile ]]
export PYTHONDONTWRITEBYTECODE=1
export GSETTINGS_BACKEND=memory
meson setup /build/compile /src --prefix=/usr --libdir=lib --buildtype=release \
    --wrap-mode=nofallback -Dbuild_gtk4=true -Dlegacy_library=false \
    -Dsystemd=enabled -Dudev=enabled -Dintrospection=true \
    -Ddesktop_docs=false -Dgtk_doc=false -Ddebug_tools=false -Dinstalled_tests=false \
    > /build/configure.log 2>&1
ninja -C /build/compile -j4 > /build/compile.log 2>&1
meson test -C /build/compile --no-rebuild --print-errorlogs > /build/upstream-tests.log 2>&1
DESTDIR=/stage meson install -C /build/compile --no-rebuild > /build/stage.log 2>&1
# The original languages target is in the legacy test-selection branch, but
# exercises the identical common base API also compiled by the modern library.
cc -DG_LOG_DOMAIN='"GnomeDesktop"' -I/build/compile/libgnome-desktop \
    -I/stage/usr/include/gnome-desktop-4.0 \
    /src/tests/languages.c -L/stage/usr/lib -Wl,-rpath,/stage/usr/lib \
    $(PKG_CONFIG_PATH=/stage/usr/lib/pkgconfig pkg-config --cflags --libs gnome-desktop-4 gio-2.0) \
    -o /build/original-languages
LD_LIBRARY_PATH=/stage/usr/lib /build/original-languages --tap > /build/original-languages.log 2>&1
cc -Wall -Wextra -Werror /src/toddy-probe.c \
    -I/stage/usr/include/gnome-desktop-4.0 -L/stage/usr/lib -Wl,-rpath,/stage/usr/lib \
    $(PKG_CONFIG_PATH=/stage/usr/lib/pkgconfig pkg-config --cflags --libs gnome-desktop-4 gio-2.0) \
    -o /build/consumer
LD_LIBRARY_PATH=/stage/usr/lib /build/consumer > /build/consumer.log 2>&1
python3 - <<'PY'
from pathlib import Path
import json,re
w=Path('/build')
rows=[json.loads(s) for s in (w/'compile/meson-logs/testlog.json').read_text().splitlines() if s.strip()]
assert rows and all(r['result']=='OK' and r['returncode']==0 for r in rows)
text=(w/'original-languages.log').read_text()
assert re.search(r'^ok\s+1\s+/languages/using-null-locale$',text,re.M)
assert not re.search(r'^not ok|#\s*SKIP',text,re.M)
(w/'test-results.json').write_text(json.dumps({
    'scope':'Native GNOME Desktop modern common API/background XML and ISO/keyboard data only; no actual session/display/wall-clock UI/thumbnail sandbox/event acceptance',
    'registered_drivers':[{'name':r['name'],'result':r['result'],'exit':r['returncode']} for r in rows],
    'original_languages_cases':1,'staged_consumer_exit':0,
    'profile':'Modern GTK4/base/background/RR/GI, systemd+udev; no legacy GTK3 desktop library, debug tools or API docs',
    'not_selected':'Legacy wall-clock driver requires broader locale fixture and contains an upstream FIXME skip; deferred, not a pass. Actual time/settings/thumbnail/display integration remains pending.'
},indent=2)+'\n')
PY
