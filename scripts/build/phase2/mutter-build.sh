#!/bin/bash
set -euo pipefail
[[ $(id -u) == 101 && ! -e /build/compile ]]
ulimit -c 0
export PYTHONDONTWRITEBYTECODE=1
meson setup /build/compile /src --prefix=/usr --libdir=lib --sysconfdir=/etc --buildtype=release \
    --wrap-mode=nofallback -Dtests=disabled -Dinstalled_tests=false -Dprofiler=false \
    -Dbash_completion=false -Ddocs=false -Ddevkit=disabled -Dxwayland=false \
    -Dopengl=false -Dgles2=true -Degl=true -Dnative_backend=true \
    -Dlogind=true -Dudev=true -Dlibwacom=true -Dlibgnome_desktop=true \
    -Dsound_player=true -Dremote_desktop=true -Dintrospection=true \
    > /build/configure.log 2>&1
ninja -C /build/compile -j4 > /build/compile.log 2>&1
meson test -C /build/compile --no-rebuild --print-errorlogs > /build/upstream-tests.log 2>&1
mkdir /build/portable-tests
for name in rectangle region time-utils dispose-bin; do
    cc -UG_DISABLE_ASSERT -I/build/compile -I/src/mtk -I/build/compile/mtk \
        /src/src/tests/mtk/$name-tests.c -L/build/compile/mtk/mtk \
        -Wl,-rpath,/build/compile/mtk/mtk -lmutter-mtk-18 \
        $(pkg-config --cflags --libs glib-2.0 gobject-2.0 graphene-gobject-1.0 pixman-1) -lm \
        -o /build/portable-tests/$name
    /build/portable-tests/$name --tap > /build/portable-tests/$name.log 2>&1
done
DESTDIR=/stage meson install -C /build/compile --no-rebuild > /build/stage.log 2>&1
export LD_LIBRARY_PATH=/stage/usr/lib/mutter-18:/stage/usr/lib
export GI_TYPELIB_PATH=/stage/usr/lib/mutter-18
/stage/usr/bin/mutter --version > /build/native-version.log 2>&1
python3 - <<'PY'
from pathlib import Path
import gi,hashlib,json,re,shutil,subprocess
w=Path('/build');rows=[json.loads(s) for s in (w/'compile/meson-logs/testlog.json').read_text().splitlines() if s.strip()]
assert rows and all(r['result']=='OK' and r['returncode']==0 for r in rows)
original=[]
for name in ['rectangle','region','time-utils','dispose-bin']:
    text=(w/('portable-tests/'+name+'.log')).read_text();cases=re.findall(r'^ok [0-9]+ .*$',text,re.M)
    assert cases and not any('# SKIP' in s for s in cases)
    original.append({'name':name,'exit':0,'passed_cases':len(cases)})
assert '50.4' in (w/'native-version.log').read_text()
for name in ['Mtk','Cogl','Clutter','Meta']:gi.require_version(name,'18')
from gi.repository import Mtk,Cogl,Clutter,Meta
union=w/'schema-union';union.mkdir();inputs={}
for base in [Path('/usr/share/glib-2.0/schemas'),Path('/stage/usr/share/glib-2.0/schemas')]:
    for path in base.iterdir():
        if path.name=='gschemas.compiled':continue
        assert path.is_file() and not path.is_symlink();sha=hashlib.sha256(path.read_bytes()).hexdigest()
        assert path.name not in inputs or inputs[path.name]==sha
        inputs[path.name]=sha;shutil.copyfile(path,union/path.name)
subprocess.run(['glib-compile-schemas','--strict',str(union)],check=True)
(w/'test-results.json').write_text(json.dumps({'scope':'Mutter Wayland/GLES2 native-backend bootstrap, original portable Mtk/GVDB and installed-layout CLI/GI/private schema checks; no actual compositor/window/session acceptance','registered_portable_drivers':[{'name':r['name'],'exit':r['returncode']} for r in rows],'original_mtk_drivers':original,'staged_cli_exit':0,'staged_gi_exit':0,'schema_cache_sha256':hashlib.sha256((union/'gschemas.compiled').read_bytes()).hexdigest(),'schema_inputs':inputs,'profile':'Wayland/EGL/GLES2 native backend, logind/udev/Wacom/GnomeDesktop/Pipewire remote APIs. Xwayland/OpenGL desktop/MDK/Sysprof omitted; no remote service automatically enabled. Original display/KVM/X11 suites not selected, no fabricated pass.','next':'Qualified same-owner shared schema integration plus actual native compositor/display tests before graphical acceptance'},indent=2)+'\n')
PY
