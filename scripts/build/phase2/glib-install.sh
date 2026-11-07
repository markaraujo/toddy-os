#!/bin/bash
# Separate full-root-verified native transaction; compile namespace stays unprivileged.
set -euo pipefail
source /opt/toddy-build/scripts/build/h06/common.sh
cd /opt/toddy-build
python3 - <<'GATE'
import json
from pathlib import Path
d=json.loads(Path('status.json').read_text())
assert d['gates']['G1']=='passed' and d['owner_review']['phase_2_approved'] is True
assert next(r for r in d['milestones'] if r['id']=='B01')['status']=='in_progress'
GATE
python3 - <<'VERIFY'
import json,sys,shutil
from pathlib import Path
sys.path.insert(0,'scripts/build/phase2')
from verify_stage import inspect_stage
work=Path('/mnt/lfs/sources/phase2/work/glib-bootstrap-1')
tests=[json.loads(line) for line in (work/'compile/meson-logs/testlog.json').read_text().splitlines()]
expected={'mainloop','gvariant','asyncqueue','basics-gobject','properties','signals',
          'gdbus-message','gdbus-serialization','gdbus-introspection','gdbus-auth',
          'gdbus-close-pending','gdbus-proxy','gdbus-connection-loss','gdbus-method-invocation'}
assert len(tests)==len(expected) and {t['name'].split(':')[-1] for t in tests}==expected
assert all(t['result']=='OK' and not t['is_fail'] and t['returncode']==0 for t in tests)
before=inspect_stage(work/'stage')
destination=Path('/mnt/lfs/sources/stage/phase2-glib-bootstrap')
assert not destination.exists(), 'Inspect existing stage before replay'
shutil.copytree(work/'stage',destination,symlinks=True)
assert inspect_stage(destination)==before
Path('/var/log/toddy/phase2').mkdir(exist_ok=True)
Path('/var/log/toddy/phase2/glib-bootstrap-stage.json').write_text(json.dumps(before,indent=2)+'\n')
VERIFY
install -Dm644 "$LFS/sources/phase2/inputs/glib-2.88.3/COPYING" \
    "$LFS/sources/stage/phase2-glib-bootstrap/usr/share/doc/glib/copyright"
python3 scripts/build/stage_package.py glib 2.88.3-1+toddy1 \
    "$LFS/sources/stage/phase2-glib-bootstrap" \
    --source glib-2.88.3.tar.xz --recipe scripts/build/phase2/glib-install.sh \
    --depends 'glibc (>= 2.44-1), libffi (>= 3.8.0-1), pcre2 (>= 10.49-1), util-linux (>= 2.42.4-1), zlib (>= 1.3.2-1)' --install
chroot "$LFS" /usr/sbin/ldconfig
