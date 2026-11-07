#!/bin/bash
set -euo pipefail
source /opt/toddy-build/scripts/build/h06/common.sh
cd /opt/toddy-build
python3 - <<'VERIFY'
from pathlib import Path
import json,sys,shutil
sys.path.insert(0,'scripts/build/phase2')
from verify_stage import inspect_stage
work=Path('/mnt/lfs/sources/phase2/work/introspection-bootstrap-1')
import hashlib
raw=(work/'validation/original-testlog.json').read_bytes()
tests=[json.loads(line) for line in raw.splitlines()]
expected={'cmph-bdz-test','gthash-test','test_ccompiler.py','test_shlibs.py',
          'test_sourcescanner.py','test_transformer.py','test_xmlwriter.py','test_pkgconfig.py',
          'test_scanner.py','test_maintransformer.py','test_patterns.py','test_parser.py'}
assert len(tests)==len(expected) and {r['name'].split(':')[-1] for r in tests}==expected
qualification=json.loads((work/'validation/qualification.json').read_text())
assert qualification['adapter_sha256']==hashlib.sha256(Path('scripts/build/phase2/qualify_introspection_tests.py').read_bytes()).hexdigest()
assert qualification['original_log_sha256']==hashlib.sha256(raw).hexdigest()
assert qualification['original_groups']==12 and qualification['unchanged_passing_groups']==11
assert qualification['corrected_test_exit']==0 and qualification['live_preprocessor_exit']==0
assert qualification['corrected_log_sha256']==hashlib.sha256((work/'validation/ccompiler-corrected.log').read_bytes()).hexdigest()
assert qualification['corrected_test_sha256']==hashlib.sha256((work/'validation/test_ccompiler.py').read_bytes()).hexdigest()
assert all(r['result']=='OK' and r['returncode']==0 and not r['is_fail'] for r in tests if not r['name'].endswith(':test_ccompiler.py'))
source=work/'stage';before=inspect_stage(source)
destination=Path('/mnt/lfs/sources/stage/phase2-introspection-bootstrap')
assert not destination.exists(), 'Inspect existing stage before replay'
shutil.copytree(source,destination,symlinks=True)
assert inspect_stage(destination)==before
assert not (destination/'usr/share/gir-1.0/GLib-2.0.gir').exists()
Path('/var/log/toddy/phase2/introspection-bootstrap-stage.json').write_text(json.dumps(before,indent=2)+'\n')
VERIFY
input=$LFS/sources/phase2/inputs/gobject-introspection-1.86.0
stage=$LFS/sources/stage/phase2-introspection-bootstrap
install -d "$stage/usr/share/doc/gobject-introspection"
cat "$input/COPYING" "$input/COPYING.GPL" "$input/COPYING.LGPL" > "$stage/usr/share/doc/gobject-introspection/copyright"
python3 scripts/build/stage_package.py gobject-introspection 1.86.0-1+toddy1 \
    "$stage" --source gobject-introspection-1.86.0.tar.xz \
    --recipe scripts/build/phase2/introspection-install.sh \
    --depends 'glib (>= 2.88.3-1), libffi (>= 3.8.0-1), python (>= 3.14.10-1), setuptools (>= 84.0.0-1)' --install
chroot "$LFS" /usr/sbin/ldconfig
