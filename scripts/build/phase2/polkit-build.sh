#!/bin/bash
# UNQUALIFIED original127 library-only diagnosis, no daemon/stage/install.
set -euo pipefail
[[ $(id -u) == 101 && -f /src/src/polkit/polkitsubject.c ]]
meson setup /build/compile /src --prefix=/usr --libdir=lib --buildtype=release \
    --wrap-mode=nofallback -Dlibs-only=true -Dtests=false -Dintrospection=false \
    -Dman=false -Dgettext=false -Dos_type=lfs -Dsession_tracking=logind -Dauthfw=pam
python3 - <<'PY'
from pathlib import Path
import json,subprocess
p=Path('/build/compile');rows=json.loads((p/'meson-info/intro-targets.json').read_text());row,=[r for r in rows if r['name']=='polkit-gobject-1' and r['type']=='shared library'];filename,=row['filename']
subprocess.run(['ninja','-C',str(p),'-j4',str(Path(filename).relative_to(p))],check=True)
PY
cc -Wall -Wextra -Werror -D_POLKIT_COMPILATION -I/src/src -I/build/compile/src \
    /src/toddy-probe.c -L/build/compile/src/polkit -Wl,-rpath,/build/compile/src/polkit \
    $(pkg-config --cflags --libs gio-2.0 gio-unix-2.0 glib-2.0) -lpolkit-gobject-1 -o /build/subject-consumer
G_DEBUG=fatal-warnings /build/subject-consumer > /build/original-subject-diagnosis.json
python3 - <<'PY'
from pathlib import Path
import hashlib,json
p=Path('/build');proof=json.loads((p/'original-subject-diagnosis.json').read_text());assert proof['malformed_unsigned_uid_accepted'] and proof['duplicate_uid_accepted'] and proof['valid_signed_uid_accepted']
proof['package_promotable']=False;proof['source_sha256']=hashlib.sha256(Path('/src/src/polkit/polkitsubject.c').read_bytes()).hexdigest();proof['next']='Narrow strict field/type/error correction and original native suite plus live authorization/credential tests required; no daemon or package installed.'
(p/'diagnosis-results.json').write_text(json.dumps(proof,indent=2)+'\n')
PY
