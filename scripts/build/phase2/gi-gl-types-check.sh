#!/bin/bash
set -euo pipefail
source /opt/toddy-build/scripts/build/target.sh
guard_target
chroot "$LFS" /usr/bin/python3 -B - <<'PYTHON' > /var/log/toddy/phase2/gi-gl-types-installed-consumer.json
import gi,json,hashlib
from pathlib import Path
gi.require_version('GL','1.0')
from gi.repository import GL
assert GL._version=='1.0'
p=Path('/usr/share/gir-1.0/GL-1.0.gir');assert hashlib.sha256(p.read_bytes()).hexdigest()=='3a45fd8a802c84ac66099d10f7f64a89a28f678be623f6fde61962e0924db849'
print(json.dumps({'scope':'Native installed exact original GL declarations/GIR/typelib import, no legacy GL call/provider/GPU or GUI acceptance','native_import_exit':0,'source_sha256':hashlib.sha256(p.read_bytes()).hexdigest()}))
PYTHON
