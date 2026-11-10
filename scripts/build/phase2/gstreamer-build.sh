#!/bin/bash
set -euo pipefail
[[ $(id -u) == 101 && ! -e /build/compile ]]
export PYTHONDONTWRITEBYTECODE=1
ulimit -c 0
meson setup /build/compile /src --prefix=/usr --libdir=lib --sysconfdir=/etc \
 --buildtype=release --wrap-mode=nodownload -Dgst_debug=false -Dintrospection=enabled \
 -Dtests=enabled -Dcheck=enabled -Dtools=enabled -Dexamples=disabled \
 -Dbenchmarks=disabled -Ddoc=disabled -Dptp-helper=disabled \
 -Dlibunwind=disabled -Dlibdw=disabled -Dbash-completion=disabled
ninja -C /build/compile -j4
meson introspect /build/compile --tests > /build/original-registered-tests.json
set +e
meson test -C /build/compile --print-errorlogs -j2 > /build/original-tests.log 2>&1
result=$?
set -e
printf '%s\n' "$result" > /build/original-tests.exit
[[ $result == 0 ]]
meson install -C /build/compile --destdir /stage --no-rebuild
export LD_LIBRARY_PATH=/stage/usr/lib
export GI_TYPELIB_PATH=/stage/usr/lib/girepository-1.0
export GST_PLUGIN_SYSTEM_PATH_1_0=''
export GST_PLUGIN_PATH_1_0=/stage/usr/lib/gstreamer-1.0
export GST_PLUGIN_SCANNER_1_0=/stage/usr/libexec/gstreamer-1.0/gst-plugin-scanner
export GST_REGISTRY_1_0=/build/consumer-registry.bin
python3 /src/toddy-probe.py > /build/native-consumer.json
/stage/usr/bin/gst-inspect-1.0 --version > /build/CLI-version.log
python3 - <<'PY'
from pathlib import Path
import hashlib,json
p=Path('/build');rows=[json.loads(s) for s in (p/'compile/meson-logs/testlog.json').read_text().splitlines() if s.strip()]
assert rows and all(r['result'] in ['OK','SKIP','EXPECTEDFAIL'] for r in rows)
r={'scope':'Frozen GStreamer core/Check/CLI/GI with original core suites in private loopback-only namespace; PTP privileged clock helper/backtrace extras/docs/examples omitted. Own raw caps/buffer/two synthetic fakesrc-EOS-stop cycles/missing-element refusal only; no hardware codecs/audio/GNOME screencast acceptance.','compile_exit':0,'stage_exit':0,'original_tests':[{k:r[k] for k in ['name','result','returncode']} for r in rows],'consumer':json.loads((p/'native-consumer.json').read_text()),'artifacts':{str(f.relative_to(p/'compile')):hashlib.sha256(f.read_bytes()).hexdigest() for f in (p/'compile').rglob('*') if f.is_file() and not f.is_symlink() and f.open('rb').read(4)==b'\x7fELF'},'stage_sha256':{str(f.relative_to(p/'stage')):hashlib.sha256(f.read_bytes()).hexdigest() for f in (p/'stage').rglob('*') if f.is_file() and not f.is_symlink()}}
(p/'stage-results.json').write_text(json.dumps(r,indent=2)+'\n')
PY
