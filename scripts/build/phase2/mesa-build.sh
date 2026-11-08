#!/bin/bash
set -euo pipefail
[[ $(id -u) == 101 && ! -e /build/compile ]]
ulimit -c 0
export PYTHONDONTWRITEBYTECODE=1 XDG_CACHE_HOME=/build/cache
python3 - <<'PY'
import os
# Four GiB scratch above the persistent sixteen GiB reserve for this profile.
fs=os.statvfs('/build');assert fs.f_bavail*fs.f_frsize>=20*1024**3
PY
meson setup /build/compile /src --prefix=/usr --libdir=lib --buildtype=release --wrap-mode=nofallback \
    -Dplatforms=wayland -Dgallium-drivers=llvmpipe,softpipe,virgl,svga -Dvulkan-drivers=[] \
    -Dllvm=enabled -Dshared-llvm=enabled -Dglx=disabled -Dglvnd=disabled \
    -Degl=enabled -Dgbm=enabled -Dgles1=disabled -Dgles2=enabled \
    -Dgallium-va=disabled -Dgallium-rusticl=false -Dvideo-codecs=[] \
    -Dvalgrind=disabled -Dlibunwind=disabled -Dlmsensors=disabled -Dbuild-tests=true
ninja -C /build/compile -j4
# These registered test dependencies are explicitly build_by_default:false.
ninja -C /build/compile -j4 src/compiler/glsl/glcpp/glcpp src/compiler/glsl/glsl_compiler
python3 - <<'PY'
from pathlib import Path
import hashlib,json
rows={}
for p in Path('/build/compile').rglob('*'):
    if not p.is_file() or p.is_symlink():continue
    with p.open('rb') as f:elf=f.read(4)==b'\x7fELF'
    if elf:
        with p.open('rb') as f:rows[str(p.relative_to('/build'))]=hashlib.file_digest(f,'sha256').hexdigest()
assert rows;Path('/build/compiled-binaries.json').write_text(json.dumps(rows,indent=2)+'\n')
PY
meson test -C /build/compile --no-rebuild --print-errorlogs --num-processes 4 --timeout-multiplier 4
DESTDIR=/stage ninja -C /build/compile install
cc -Wall -Wextra -Werror /src/toddy-probe.c -I/stage/usr/include -L/stage/usr/lib -Wl,-rpath-link,/stage/usr/lib \
    $(PKG_CONFIG_PATH=/stage/usr/lib/pkgconfig pkg-config --cflags --libs egl glesv2) -o /build/mesa-consumer
export LD_LIBRARY_PATH=/stage/usr/lib LIBGL_DRIVERS_PATH=/stage/usr/lib/dri
export LIBGL_ALWAYS_SOFTWARE=1 GALLIUM_DRIVER=llvmpipe EGL_PLATFORM=surfaceless
/build/mesa-consumer > /build/native-render.log
python3 - <<'PY'
from pathlib import Path
import hashlib,json,os
p=Path('/build/compile/meson-logs/testlog.json');rows=[json.loads(line) for line in p.read_text().splitlines()]
assert rows and all((r['result']=='OK' and r['returncode']==0) or (r['result']=='SKIP' and r['returncode']==77) for r in rows)
render=Path('/build/native-render.log');text=render.read_text();assert 'renderer: llvmpipe' in text
pixel=[int(v) for line in text.splitlines() if line.startswith('pixel: ') for v in line.removeprefix('pixel: ').split()]
assert len(pixel)==4 and pixel[0]==0 and abs(pixel[1]-32)<=1 and abs(pixel[2]-64)<=1 and pixel[3]==255
before=json.loads(Path('/build/compiled-binaries.json').read_text())
for relative,sha in before.items():
    with (Path('/build')/relative).open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==sha,relative
fs=os.statvfs('/build');assert fs.f_bavail*fs.f_frsize>=16*1024**3
Path('/build/test-results.json').write_text(json.dumps({'scope':'Reference software/virtual Wayland EGL/GBM profile, native CPU shader/raster/pixel proof; not GNOME/window/hardware acceptance','registered_tests':len(rows),'tests':[{'name':r['name'],'result':r['result'],'returncode':r['returncode']} for r in rows],'upstream_log_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'consumer_exit':0,'native_render_stdout':render.read_text(),'native_render_sha256':hashlib.sha256(render.read_bytes()).hexdigest(),'unchanged_compiled_elfs':len(before),'free_bytes_after_build':fs.f_bavail*fs.f_frsize},indent=2)+'\n')
PY
