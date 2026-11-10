#!/bin/bash
set -euo pipefail
[[ $(id -u) == 101 && ! -e /build/compile ]]
export PYTHONDONTWRITEBYTECODE=1
ulimit -c 0
meson setup /build/compile /src --prefix=/usr --libdir=lib --sysconfdir=/etc \
 --buildtype=release --wrap-mode=nodownload -Dintrospection=enabled -Dtests=enabled \
 -Dtools=enabled -Dexamples=disabled -Ddoc=disabled -Dorc=disabled -Dorc-compiler=disabled \
 -Dalsa=enabled -Dogg=enabled -Dvorbis=enabled -Dpango=enabled -Diso-codes=enabled \
 -Dcdparanoia=disabled -Dlibvisual=disabled -Dopus=disabled -Dtheora=disabled \
 -Dtremor=disabled -Dx11=disabled -Dxshm=disabled -Dxvideo=disabled -Dxi=disabled \
 -Dqt5=disabled -Dgl=enabled -Dgl_api=gles2 -Dgl_platform=egl \
 -Dgl_winsys=wayland,egl,surfaceless,gbm -Dgl-graphene=enabled -Dgl-jpeg=enabled -Dgl-png=enabled
ninja -C /build/compile -j4
meson introspect /build/compile --tests > /build/original-registered-tests.json
python3 - <<'PY'
from pathlib import Path
import json,subprocess
p=Path('/build');rows=json.loads((p/'original-registered-tests.json').read_text())
# Actual GL contexts require native session/device infrastructure; compile all,
# retain exact deferred originals, never count them as passing portable tests.
gl=[r for r in rows if any(x in r['name'] for x in ['libs_gstgl','elements_gl','pipelines_gl_'])]
portable_names={'libs_gstglapi','libs_gstglmatrix'}
deferred=[r for r in gl if r['name'].split(':')[-1] not in portable_names]
assert len(gl)==19 and len(deferred)==17
selected=[r['name'] for r in rows if r not in deferred]
assert selected
(p/'deferred-original-tests.json').write_text(json.dumps({'reason':'Original real GL context programs deferred to native session; not skipped passes or unchanged suite replay','tests':deferred},indent=2)+'\n')
with (p/'original-tests.log').open('x') as log:
 r=subprocess.run(['meson','test','-C','/build/compile','--print-errorlogs','-j2',*selected],stdout=log,stderr=subprocess.STDOUT)
(p/'original-tests.exit').write_text(str(r.returncode)+'\n');assert r.returncode==0
PY
meson install -C /build/compile --destdir /stage --no-rebuild
export LD_LIBRARY_PATH=/stage/usr/lib
export GI_TYPELIB_PATH=/stage/usr/lib/girepository-1.0
export GST_PLUGIN_PATH_1_0=/stage/usr/lib/gstreamer-1.0
export GST_PLUGIN_SYSTEM_PATH_1_0=/usr/lib/gstreamer-1.0
export GST_REGISTRY_1_0=/build/consumer-registry.bin
python3 /src/toddy-probe.py > /build/native-consumer.json
python3 - <<'PY'
from pathlib import Path
import hashlib,json
p=Path('/build');rows=[json.loads(x) for x in (p/'compile/meson-logs/testlog.json').read_text().splitlines() if x.strip()]
assert rows and all(r['result'] in ['OK','SKIP','EXPECTEDFAIL'] for r in rows)
r={'scope':'Frozen GStreamer Base1.28.6 core raw audio/video/app/playback/ALSA/Ogg/Vorbis/Pango and EGL/GLES2 Wayland/surfaceless/GBM build; ORC JIT/optional extra codecs/X11/examples omitted. Original17real GL-context programs compiled/deferred to native session, no passing claim. Actual own synthetic video red pixels/audio silence through appsink+typed Audio/Video GI/Stop/recovery only, no devices/real audio/playback/GL/GNOME screencast acceptance.','compile_exit':0,'stage_exit':0,'original_tests':[{k:r[k] for k in ['name','result','returncode']} for r in rows],'deferred_originals':json.loads((p/'deferred-original-tests.json').read_text()),'consumer':json.loads((p/'native-consumer.json').read_text()),'artifacts':{str(f.relative_to(p/'compile')):hashlib.sha256(f.read_bytes()).hexdigest() for f in (p/'compile').rglob('*') if f.is_file() and not f.is_symlink() and f.open('rb').read(4)==b'\x7fELF'},'stage_sha256':{str(f.relative_to(p/'stage')):hashlib.sha256(f.read_bytes()).hexdigest() for f in (p/'stage').rglob('*') if f.is_file() and not f.is_symlink()}}
(p/'stage-results.json').write_text(json.dumps(r,indent=2)+'\n')
PY
