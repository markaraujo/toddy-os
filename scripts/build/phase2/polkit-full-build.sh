#!/bin/bash
# Full selected runtime from authenticated corrected source; native suite next.
set -euo pipefail
[[ $(id -u) == 101 ]]
meson setup /build/compile /src --prefix=/usr --libdir=lib --libexecdir=lib/polkit-1 \
    --sysconfdir=/etc --localstatedir=/var --buildtype=release --wrap-mode=nofallback \
    -Dlibs-only=false -Dtests=true -Dintrospection=true -Dman=false -Dgettext=true \
    -Dos_type=lfs -Dsession_tracking=logind -Dauthfw=pam -Dpolkitd_user=polkitd \
    -Dprivileged_group=wheel -Dpam_include=polkit-auth
ninja -C /build/compile -j4
DESTDIR=/stage ninja -C /build/compile install
python3 - <<'PY'
from pathlib import Path
import hashlib,json,subprocess
p=Path('/build');tests=json.loads((p/'compile/meson-info/intro-tests.json').read_text());assert len(tests)==5
# Original wrappers need native user/mount namespaces: do not replay Ubuntu EPERM.
artifacts={str(f.relative_to(p/'compile')):hashlib.sha256(f.read_bytes()).hexdigest() for f in (p/'compile').rglob('*') if f.is_file() and not f.is_symlink() and f.open('rb').read(4)==b'\x7fELF'}
proof={'scope':'Full Polkit127 compiled and staged only, original five programs await native namespace gate; NO installed privilege acceptance','compile_exit':0,'stage_exit':0,'package_promotable':False,'original_tests':tests,'artifacts':artifacts,'stage_sha256':{str(f.relative_to(p/'stage')):hashlib.sha256(f.read_bytes()).hexdigest() for f in (p/'stage').rglob('*') if f.is_file() and not f.is_symlink()}}
(p/'stage-results.json').write_text(json.dumps(proof,indent=2)+'\n')
PY
