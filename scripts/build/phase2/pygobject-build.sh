#!/bin/bash
# Native GIO binding first; Cairo/GTK are later consumers of the same binding.
set -euo pipefail
[[ $(id -u) == 101 && -d /src/gi && -d /stage ]]
meson setup /build/compile /src --prefix=/usr --buildtype=release \
    --wrap-mode=nofallback -Dpycairo=disabled
ninja -C /build/compile -j8
meson test -C /build/compile --list > /build/test-list.txt
DESTDIR=/stage ninja -C /build/compile install
PYTHONPATH=/stage/usr/lib/python3.14/site-packages python3 - <<'NATIVE'
import gi
gi.require_version('Gio', '2.0')
from gi.repository import Gio, GLib
assert GLib.MAJOR_VERSION == 2 and GLib.MINOR_VERSION == 88
assert GLib.Variant('(st)', ('fixture', 42)).unpack() == ('fixture', 42)
assert Gio.File.new_for_path('/tmp/fixture').get_path() == '/tmp/fixture'
assert Gio.DBusNodeInfo.new_for_xml('<node><interface name="io.github.markaraujo.Toddy.Fixture1"/></node>')
print('NATIVE_GIO_BINDING_STAGE_PASSED')
NATIVE
