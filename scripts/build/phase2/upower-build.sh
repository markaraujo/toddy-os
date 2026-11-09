#!/bin/bash
# Frozen Linux backend; portable originals only, real service separately required.
set -euo pipefail
[[ $(id -u) == 101 && ! -e /build/compile ]]
export PYTHONDONTWRITEBYTECODE=1
meson setup /build/compile /src --prefix=/usr --libdir=lib --libexecdir=libexec \
    --sysconfdir=/etc --localstatedir=/var --buildtype=release --wrap-mode=nodownload \
    -Dgtk-doc=false -Dman=false -Dintrospection=enabled -Dpolkit=enabled \
    -Didevice=disabled -Dinstalled_tests=false -Dos_backend=linux \
    -Dhistorydir=/var/lib/upower -Dstatedir=/var/lib/upower
ninja -C /build/compile -j4
# The two omitted originals explicitly return early without a system bus.
# Do not count their success-shaped skip as acceptance in this compiler sandbox.
/build/compile/src/up_self_test --tap -x /power/polkit -x /power/daemon > /build/original-portable.log 2>&1
meson install -C /build/compile --destdir /stage --no-rebuild
export LD_LIBRARY_PATH=/stage/usr/lib
export GI_TYPELIB_PATH=/stage/usr/lib/girepository-1.0
python3 /src/toddy-probe.py /stage > /build/native-consumer.json
python3 - <<'PY'
from pathlib import Path
import hashlib,json,re
p=Path('/build');text=(p/'original-portable.log').read_text();passes=re.findall(r'^ok \d+ (/[a-z_/]+)$',text,re.M)
assert set(passes)=={'/power/backend','/power/device','/power/device_list','/power/history','/power/native'} and len(passes)==5
assert 'not ok' not in text and 'No system D-BUS running' not in text
result={'scope':'Five original portable object/history tests plus native GI/type/CLI consumer; omitted actual system-bus originals and Umockdev device matrix are not passes; no real battery/device claim','compile_exit':0,'stage_exit':0,'original_portable_cases':passes,'consumer':json.loads((p/'native-consumer.json').read_text()),'artifacts':{str(f.relative_to(p/'compile')):hashlib.sha256(f.read_bytes()).hexdigest() for f in (p/'compile').rglob('*') if f.is_file() and not f.is_symlink() and f.open('rb').read(4)==b'\x7fELF'},'stage_sha256':{str(f.relative_to(p/'stage')):hashlib.sha256(f.read_bytes()).hexdigest() for f in (p/'stage').rglob('*') if f.is_file() and not f.is_symlink()}}
(p/'stage-results.json').write_text(json.dumps(result,indent=2)+'\n')
PY
