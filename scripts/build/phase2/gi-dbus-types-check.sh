#!/bin/bash
set -euo pipefail
source /opt/toddy-build/scripts/build/target.sh
guard_target
chroot "$LFS" /usr/bin/python3 -B - <<'PYTHON' > /var/log/toddy/phase2/gi-dbus-types-installed-consumer.json
import gi,json
from pathlib import Path
gi.require_version('DBus','1.0')
from gi.repository import DBus
assert int(DBus.BusType.SESSION)==0 and int(DBus.BusType.SYSTEM)==1
assert Path('/usr/share/gir-1.0/DBus-1.0.gir').is_file()
print(json.dumps({'scope':'Installed declarative DBus GIR/type enum consumer, not full D-Bus or GUI acceptance','native_enum_exit':0}))
PYTHON
