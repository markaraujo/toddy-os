#!/bin/bash
# Original keyboard stages/binaries are preserved; only newly affected checks run.
set -euo pipefail
[[ $(id -u) == 101 && -d /build/compile-data && -d /build/compile-lib && ! -e /build/qualified.json ]]
ulimit -c 0
export PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1
export PYTEST_ADDOPTS='-o cache_dir=/build/pytest-cache'
export XKBCOMMON_LIB_PATH=/stage/libxkbcommon/usr/lib/libxkbcommon.so.0
export LD_LIBRARY_PATH=/stage/libxkbcommon/usr/lib
export XKB_CONFIG_ROOT=/stage/xkeyboard-config/usr/share/xkeyboard-config-2
python3 - <<'PY'
from pathlib import Path
import hashlib,json,os
root=Path('/build');destination=root/'resume-2-before.json';assert not destination.exists()
rows=[json.loads(line) for line in (root/'compile-lib/meson-logs/keyboard-lib-testlog.json').read_text().splitlines()]
assert len(rows)==26 and all(r['result']=='OK' and r['returncode']==0 for r in rows)
payload={}
for path in (root/'compile-lib').rglob('*'):
    if path.is_file() and not path.is_symlink():
        with path.open('rb') as stream:elf=stream.read(4)==b'\x7fELF'
        if elf:payload[str(path.relative_to(root))]=hashlib.sha256(path.read_bytes()).hexdigest()
stages={}
for name in ['xkeyboard-config','libxkbcommon']:
    prefix=Path('/stage')/name;entries={}
    for path in sorted(prefix.rglob('*')):
        relative=str(path.relative_to(prefix))
        if path.is_symlink():entries[relative]={'symlink':os.readlink(path)}
        elif path.is_file():entries[relative]={'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'size':path.stat().st_size}
    stages[name]=entries
assert payload and all(stages.values())
destination.write_text(json.dumps({'binaries':payload,'stages':stages,'library_log_sha256':hashlib.sha256((root/'compile-lib/meson-logs/keyboard-lib-testlog.json').read_bytes()).hexdigest()},indent=2)+'\n')
PY
# New native X11 locale/Compose data affects these two registered library drivers.
meson test -C /build/compile-lib --no-rebuild --print-errorlogs context compose --logbase keyboard-locale-recheck
# The full original data driver has8680 cases and thousands of compiler launches.
# A larger timeout permits completion; only its actual terminal result is accepted.
meson test -C /build/compile-data --no-rebuild --print-errorlogs --timeout-multiplier 20 --logbase keyboard-data-resume
export PKG_CONFIG_PATH=/stage/libxkbcommon/usr/lib/pkgconfig:/stage/xkeyboard-config/usr/share/pkgconfig
cc -I/stage/libxkbcommon/usr/include /src/toddy-probe.c -L/stage/libxkbcommon/usr/lib \
    $(pkg-config --cflags --libs xkbcommon xkbregistry) -o /build/keyboard-consumer
/build/keyboard-consumer /stage/xkeyboard-config/usr/share/xkeyboard-config-2
python3 - <<'PY'
from pathlib import Path
import hashlib,json,os
root=Path('/build');before=json.loads((root/'resume-2-before.json').read_text());reports=[]
for name,directory,base,count in [('library','compile-lib','keyboard-lib-testlog',26),('locale-recheck','compile-lib','keyboard-locale-recheck',2),('data','compile-data','keyboard-data-resume',1)]:
    path=root/directory/'meson-logs'/(base+'.json');rows=[json.loads(line) for line in path.read_text().splitlines()]
    assert len(rows)==count and all(r['result']=='OK' and r['returncode']==0 for r in rows),name
    reports.append({'name':name,'drivers':len(rows),'exit':0,'log_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'tests':[r['name'] for r in rows]})
for relative,sha in before['binaries'].items():assert hashlib.sha256((root/relative).read_bytes()).hexdigest()==sha,relative
for name,expected in before['stages'].items():
    prefix=Path('/stage')/name;entries={}
    for path in sorted(prefix.rglob('*')):
        relative=str(path.relative_to(prefix))
        if path.is_symlink():entries[relative]={'symlink':os.readlink(path)}
        elif path.is_file():entries[relative]={'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'size':path.stat().st_size}
    assert entries==expected,name
proof={'scope':'Native staged minimal Wayland keyboard APIs/data, original library26 plus affected locale2 and full upstream data driver; no physical/GUI input proof',
       'reports':reports,'stages':before['stages'],'consumer_exit':0,'us_br_pt_shift_registry':True,
       'unchanged_library_elfs':len(before['binaries']),'relative_compatibility_link':'usr/share/X11/xkb -> ../xkeyboard-config-2',
       'recovery':'Original keyboard1 failure retained: absent Xorg comparator and60s timeout. Native xkbcomp1.5.0 supplied; same library/data stages reused, no rebuild.'}
(root/'qualified.json').write_text(json.dumps(proof,indent=2)+'\n')
PY
