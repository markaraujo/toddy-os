#!/bin/bash
# Frozen BLFS13.1 GtkSourceView5.20; widget drivers await real native display.
set -euo pipefail
[[ $(id -u) == 101 && -f /src/meson.build && -d /stage ]]
meson setup /build/compile /src --prefix=/usr --libdir=lib --buildtype=release \
    --wrap-mode=nofallback -Dintrospection=enabled -Dvapi=false \
    -Ddocumentation=false -Dsysprof=false -Dbuild-testsuite=true -Dinstall-tests=false
ninja -C /build/compile -j4
DESTDIR=/stage ninja -C /build/compile install
export PKG_CONFIG_PATH=/stage/usr/lib/pkgconfig
cc -Wall -Wextra -Werror /src/toddy-probe.c -o /build/native-consumer \
    -I/stage/usr/include/gtksourceview-5 -L/stage/usr/lib -Wl,-rpath,/stage/usr/lib \
    $(pkg-config --cflags --libs gtksourceview-5)
/build/native-consumer > /build/native-consumer.log 2>&1
GI_TYPELIB_PATH=/stage/usr/lib/girepository-1.0 LD_LIBRARY_PATH=/stage/usr/lib python3 -B - <<'GI' > /build/native-gi.log 2>&1
import gi
gi.require_version('GtkSource','5')
from gi.repository import GtkSource
assert (GtkSource.get_major_version(),GtkSource.get_minor_version(),GtkSource.get_micro_version())==(5,20,0)
assert GtkSource.Encoding.get_from_charset('UTF-8') is not None
assert GtkSource.Encoding.get_from_charset('TODDY-INVALID-ENCODING') is None
GI
python3 - <<'PY'
import hashlib,json
from pathlib import Path
registered=json.loads(Path('/build/compile/meson-info/intro-tests.json').read_text())
assert registered
artifacts={str(p.relative_to('/build')):hashlib.sha256(p.read_bytes()).hexdigest() for p in Path('/build/compile').rglob('*') if p.is_file() and not p.is_symlink() and p.read_bytes()[:4]==b'\x7fELF'}
Path('/build/stage-results.json').write_text(json.dumps({'scope':'Native compile/data/ABI only; original display drivers still pending, no promotion or editor/UI acceptance','native_build_exit':0,'stage_exit':0,'c_version_data_exit':0,'gi_version_exit':0,'upstream_tests_state':'pending_native_display','registered_tests_pending':[r['name'] for r in registered],'compiled_elf_sha256':artifacts},indent=2)+'\n')
PY
