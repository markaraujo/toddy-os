#!/bin/bash
set -euo pipefail
[[ $(id -u) == 101 && ! -e /build/compile ]]
export PYTHONDONTWRITEBYTECODE=1
meson setup /build/compile /src --prefix=/usr --libdir=lib --sysconfdir=/etc \
 --buildtype=release --wrap-mode=nodownload -Dlibnma_gtk4=true -Dgcr=true \
 -Diso_codes=true -Dmobile_broadband_provider_info=false -Dgtk_doc=false \
 -Dintrospection=true -Dvapi=true
ninja -C /build/compile -j4
meson introspect /build/compile --tests > /build/original-registered-tests.json
python3 - <<'PY'
from pathlib import Path
import json
assert json.loads(Path('/build/original-registered-tests.json').read_text())==[], 'Review newly registered original automated tests'
PY
meson install -C /build/compile --destdir /stage --no-rebuild
for major in 3 4; do
 if [[ $major == 3 ]]; then gtk_package=gtk+-3.0; nma_library=nma; else gtk_package=gtk4; nma_library=nma-gtk4; fi
 cc /src/toddy-probe.c -DTODDY_GTK_MAJOR="$major" -I/stage/usr/include/libnma -L/stage/usr/lib \
  $(pkg-config --cflags --libs "$gtk_package" libnm) -l"$nma_library" -Wl,-rpath,/stage/usr/lib -o /build/native-probe-"$major"
 LD_LIBRARY_PATH=/stage/usr/lib /build/native-probe-"$major" > /build/native-consumer-"$major".json
done
python3 - <<'PY'
from pathlib import Path
import hashlib,json
p=Path('/build');consumers={str(major):json.loads((p/('native-consumer-'+str(major)+'.json')).read_text()) for major in [3,4]}
r={'scope':'Actual GTK3 and GTK4 libnma1.10.6/GI/Vala with owned Gcr4 certificate support and ISO codes. Source registers no automated tests; manual GTK executables compile only. Own widget type/GTK ABI and libnm refusal/recovery consumers, NOT actual widget open/focus, credentials/WiFi/network/GNOME acceptance. Optional cellular provider DB omitted.','compile_exit':0,'stage_exit':0,'original_registered_tests':[],'consumers':consumers,'artifacts':{str(f.relative_to(p/'compile')):hashlib.sha256(f.read_bytes()).hexdigest() for f in (p/'compile').rglob('*') if f.is_file() and not f.is_symlink() and f.open('rb').read(4)==b'\x7fELF'},'stage_sha256':{str(f.relative_to(p/'stage')):hashlib.sha256(f.read_bytes()).hexdigest() for f in (p/'stage').rglob('*') if f.is_file() and not f.is_symlink()}}
(p/'stage-results.json').write_text(json.dumps(r,indent=2)+'\n')
PY
