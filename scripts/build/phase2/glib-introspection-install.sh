#!/bin/bash
set -euo pipefail
source /opt/toddy-build/scripts/build/h06/common.sh
cd /opt/toddy-build
python3 - <<'VERIFY'
from pathlib import Path
import json,sys,hashlib,shutil
sys.path.insert(0,'scripts/build/phase2')
from verify_stage import inspect_stage
work=Path('/mnt/lfs/sources/phase2/work/glib-bootstrap-1')
qualification=json.loads((work/'introspection-qualification.json').read_text())
for name,expected in qualification['after'].items():
 assert hashlib.sha256((work/'stage/usr/lib'/name).read_bytes()).hexdigest()==expected
assert qualification['core_checks'] in ['reused identical libraries','14 affected groups rerun passed']
for name in qualification['required_typelibs']:
 assert (work/('stage/usr/lib/girepository-1.0/'+name+'.typelib')).is_file()
source=work/'stage';before=inspect_stage(source)
destination=Path('/mnt/lfs/sources/stage/phase2-glib-introspection')
assert not destination.exists(), 'Inspect existing stage before replay'
shutil.copytree(source,destination,symlinks=True)
assert inspect_stage(destination)==before
Path('/var/log/toddy/phase2/glib-introspection-stage.json').write_text(json.dumps(before,indent=2)+'\n')
VERIFY
stage=$LFS/sources/stage/phase2-glib-introspection
install -Dm644 "$LFS/sources/phase2/inputs/glib-2.88.3/COPYING" "$stage/usr/share/doc/glib/copyright"
python3 scripts/build/stage_package.py glib 2.88.3-1+toddy2 "$stage" \
    --source glib-2.88.3.tar.xz --recipe scripts/build/phase2/glib-introspection-install.sh \
    --depends 'glibc (>= 2.44-1), libffi (>= 3.8.0-1), pcre2 (>= 10.49-1), util-linux (>= 2.42.4-1), zlib (>= 1.3.2-1)' --install
chroot "$LFS" /usr/sbin/ldconfig
