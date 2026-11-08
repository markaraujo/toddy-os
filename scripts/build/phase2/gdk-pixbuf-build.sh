#!/bin/bash
set -euo pipefail
[[ $(id -u) == 101 && ! -e /build/compile ]]
ulimit -c 0
export PYTHONDONTWRITEBYTECODE=1
meson setup /build/compile /src --prefix=/usr --libdir=lib --buildtype=release --wrap-mode=nofallback \
    -Dpng=enabled -Djpeg=enabled -Dgif=enabled -Dtiff=disabled -Dglycin=disabled -Dothers=disabled \
    -Dbuiltin_loaders=png,jpeg,gif -Dintrospection=enabled -Ddocumentation=false -Dman=false \
    -Dtests=true -Dinstalled_tests=false -Dthumbnailer=enabled
ninja -C /build/compile -j4
meson test -C /build/compile --no-rebuild --print-errorlogs --num-processes 4 --timeout-multiplier 4
DESTDIR=/stage ninja -C /build/compile install
python3 - <<'PY'
from pathlib import Path
import hashlib,json,shutil
# DESTDIR suppresses upstream global cache writes. Retain the actual generated
# native test cache; this profile has no external modules, only builtin loaders.
p=Path('/build/compile/gdk-pixbuf/loaders.cache');text=p.read_text()
assert text and all(not line.strip() or line.startswith('#') for line in text.splitlines())
assert all(s not in text for s in ['/build/','/src/','/stage/'])
out=Path('/stage/usr/lib/gdk-pixbuf-2.0/2.10.0/loaders.cache');assert not out.exists()
out.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,out)
Path('/build/generated-cache.json').write_text(json.dumps({'scope':'Actual native generated empty external-loader cache; PNG/JPEG/GIF builtin, future SVG acquisition requires controlled cache update',
    'path':'usr/lib/gdk-pixbuf-2.0/2.10.0/loaders.cache','sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'external_module_records':0},indent=2)+'\n')
PY
cc -Wall -Wextra -Werror /src/toddy-probe.c -I/stage/usr/include/gdk-pixbuf-2.0 -L/stage/usr/lib \
    $(PKG_CONFIG_PATH=/stage/usr/lib/pkgconfig pkg-config --cflags --libs gdk-pixbuf-2.0 gio-2.0) -o /build/pixbuf-consumer
LD_LIBRARY_PATH=/stage/usr/lib GDK_PIXBUF_MODULE_FILE=/stage/usr/lib/gdk-pixbuf-2.0/2.10.0/loaders.cache /build/pixbuf-consumer > /build/native-image.log
python3 - <<'PY'
from pathlib import Path
import hashlib,json
p=Path('/build/compile/meson-logs/testlog.json');rows=[json.loads(line) for line in p.read_text().splitlines()]
assert rows and all((r['result']=='OK' and r['returncode']==0) or (r['result']=='SKIP' and r['returncode']==77) for r in rows)
Path('/build/test-results.json').write_text(json.dumps({'scope':'Native PNG/JPEG stream roundtrip, invalid image rejection and builtin PNG/JPEG/GIF registry; no window/desktop acceptance',
    'registered_tests':len(rows),'tests':[{'name':r['name'],'result':r['result'],'returncode':r['returncode']} for r in rows],
    'upstream_log_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'staged_consumer_exit':0,
    'native_image_stdout':Path('/build/native-image.log').read_text(),'generated_cache':json.loads(Path('/build/generated-cache.json').read_text()),
    'optional_loaders':'Glycin/TIFF/weakly-maintained others disabled in this initial profile; SVG still requires native librsvg loader qualification'},indent=2)+'\n')
PY
