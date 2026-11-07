#!/bin/bash
set -euo pipefail
source /opt/toddy-build/scripts/build/h06/common.sh
chroot_run <<'NATIVE'
set -euo pipefail
python3 - <<'PY'
import gi
assert gi.__version__ == '3.56.3'
assert gi.__file__.startswith('/usr/lib/python3.14/site-packages/')
gi.require_version('Gio', '2.0')
from gi.repository import Gio, GLib
assert GLib.Variant('(st)', ('native', 42)).unpack() == ('native', 42)
assert Gio.File.new_for_path('/tmp/fixture').get_basename() == 'fixture'
assert Gio.DBusNodeInfo.new_for_xml('<node><interface name="io.github.markaraujo.Toddy.Fixture1"/></node>')
PY
test -z "$(dpkg --audit)"
apt-get check
NATIVE
