#!/bin/bash
# Native compilation/ABI staging only. Widget tests require a native display.
set -euo pipefail
[[ $(id -u) == 101 && -f /src/meson.build && -d /stage ]]
meson setup /build/compile /src --prefix=/usr --libdir=lib --buildtype=release \
    --wrap-mode=nofallback -Dintrospection=enabled -Dvapi=false \
    -Ddocumentation=false -Dtests=true -Dexamples=false
ninja -C /build/compile -j4
DESTDIR=/stage ninja -C /build/compile install
export PKG_CONFIG_PATH=/stage/usr/lib/pkgconfig
cc /src/toddy-probe.c -I/stage/usr/include/libadwaita-1 -o /build/native-version \
    -L/stage/usr/lib -Wl,-rpath,/stage/usr/lib $(pkg-config --cflags --libs libadwaita-1)
/build/native-version > /build/native-version.log 2>&1
GI_TYPELIB_PATH=/stage/usr/lib/girepository-1.0 LD_LIBRARY_PATH=/stage/usr/lib python3 -B - <<'GI' > /build/native-gi-version.log 2>&1
import gi
gi.require_version('Adw','1')
from gi.repository import Adw
assert (Adw.get_major_version(),Adw.get_minor_version(),Adw.get_micro_version())==(1,9,3)
GI
python3 - <<'PY'
import json
from pathlib import Path
registered=json.loads(Path('/build/compile/meson-info/intro-tests.json').read_text())
assert registered
assert 'gtk_test_init' in Path('/src/tests/test-alert-dialog.c').read_text()
Path('/build/stage-results.json').write_text(json.dumps({'scope':'Native compilation and C/GI version ABI only; unqualified until display-dependent widget tests',
    'native_build_exit':0,'stage_exit':0,'c_version_exit':0,'gi_version_exit':0,
    'upstream_tests_state':'pending_native_display','upstream_tests_passed':0,
    'registered_tests_pending':[r['name'] for r in registered],
    'next':'Preserve this compiled cache and stage. Provide the planned native Mutter/Wayland display, then execute registered widget tests; do not promote or claim graphical acceptance from this job.'},indent=2)+'\n')
PY
