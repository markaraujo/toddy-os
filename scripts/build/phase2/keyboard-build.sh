#!/bin/bash
set -euo pipefail
[[ $(id -u) == 101 && ! -e /build/compile-data && ! -e /build/compile-lib ]]
ulimit -c 0
export PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1
export PYTEST_ADDOPTS='-o cache_dir=/build/pytest-cache'
meson setup /build/compile-data /src/xkeyboard-config-2.48 --prefix=/usr --buildtype=release --wrap-mode=nofallback
ninja -C /build/compile-data -j4
DESTDIR=/stage/xkeyboard-config ninja -C /build/compile-data install
python3 - <<'PY'
from pathlib import Path
import os
root=Path('/stage/xkeyboard-config')
link=root/'usr/share/X11/xkb'
assert link.is_symlink() and os.readlink(link)=='/usr/share/xkeyboard-config-2'
link.unlink();link.symlink_to('../xkeyboard-config-2')
assert link.resolve()==root/'usr/share/xkeyboard-config-2'
PY
export PKG_CONFIG_PATH=/stage/xkeyboard-config/usr/share/pkgconfig
meson setup /build/compile-lib /src/libxkbcommon-1.13.2 --prefix=/usr --libdir=lib \
    --buildtype=release --wrap-mode=nofallback -D enable-docs=false -D enable-x11=false \
    -D enable-wayland=true -D enable-xkbregistry=true -D xkb-config-root=/usr/share/xkeyboard-config-2
ninja -C /build/compile-lib -j4
DESTDIR=/stage/libxkbcommon ninja -C /build/compile-lib install
export XKBCOMMON_LIB_PATH=/stage/libxkbcommon/usr/lib/libxkbcommon.so.0
export LD_LIBRARY_PATH=/stage/libxkbcommon/usr/lib
export XKB_CONFIG_ROOT=/stage/xkeyboard-config/usr/share/xkeyboard-config-2
meson test -C /build/compile-lib --no-rebuild --print-errorlogs --num-processes 4 --logbase keyboard-lib-testlog
meson test -C /build/compile-data --no-rebuild --print-errorlogs --num-processes 4 --logbase keyboard-data-testlog
export PKG_CONFIG_PATH=/stage/libxkbcommon/usr/lib/pkgconfig:/stage/xkeyboard-config/usr/share/pkgconfig
cc -I/stage/libxkbcommon/usr/include /src/toddy-probe.c -L/stage/libxkbcommon/usr/lib \
    $(pkg-config --cflags --libs xkbcommon xkbregistry) -o /build/keyboard-consumer
/build/keyboard-consumer /stage/xkeyboard-config/usr/share/xkeyboard-config-2
python3 - <<'PY'
from pathlib import Path
import hashlib,json,os
root=Path('/build');reports=[]
for name,directory in [('library','compile-lib'),('data','compile-data')]:
    path=root/directory/'meson-logs'/('keyboard-'+('lib' if name=='library' else 'data')+'-testlog.json')
    rows=[json.loads(line) for line in path.read_text().splitlines()]
    assert rows and all(r['result']=='OK' and r['returncode']==0 for r in rows),name
    reports.append({'name':name,'drivers':len(rows),'exit':0,'log_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'tests':[r['name'] for r in rows]})
stages={}
for name in ['xkeyboard-config','libxkbcommon']:
    prefix=Path('/stage')/name;entries={}
    for path in sorted(prefix.rglob('*')):
        relative=str(path.relative_to(prefix))
        if path.is_symlink():entries[relative]={'symlink':os.readlink(path)}
        elif path.is_file():entries[relative]={'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'size':path.stat().st_size}
    stages[name]=entries
Path('/build/qualified.json').write_text(json.dumps({'scope':'Native staged minimal Wayland keyboard APIs/data and original registered suites; no X11/physical/GUI input proof','reports':reports,'stages':stages,'consumer_exit':0,'us_br_pt_shift_registry':True,'relative_compatibility_link':'usr/share/X11/xkb -> ../xkeyboard-config-2'},indent=2)+'\n')
PY
