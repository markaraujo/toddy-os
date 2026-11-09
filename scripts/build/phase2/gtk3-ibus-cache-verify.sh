#!/bin/bash
set -euo pipefail
source /opt/toddy-build/scripts/build/target.sh
guard_target
python3 - <<'PY'
from pathlib import Path
import hashlib,json,subprocess,sys
sys.path.insert(0,'/opt/toddy-build/scripts/build/phase2')
from schema_union_install import verify
old=json.loads(Path('/var/log/toddy/build/b02-gtk3-ibus-cache-install.failed.json').read_text());assert old['recipe_exit']==0 and old['postcheck_exit']==1
r=json.loads(Path('/var/log/toddy/packages/gtk3_3.24.52-1+toddy2_amd64.json').read_text());assert r['installed'];verify(r)
assert r['archive_sha256']=='658601ca770907cd84b191465782f814600c5dc772c51c51918a58d087fbd71e'
archive=Path('/var/cache/toddy/packages/gtk3_3.24.52-1+toddy2_amd64.deb')
with archive.open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==r['archive_sha256']
receipt=json.loads(Path('/var/log/toddy/phase2/gtk3-ibus-cache-transaction-1.json').read_text());assert receipt['state']=='complete'
query=subprocess.run(['chroot','--userspec=101:101','/mnt/lfs','gtk-query-immodules-3.0',*sorted(receipt['modules'])],env={'PATH':'/usr/bin:/usr/sbin','LC_ALL':'C.UTF-8','HOME':'/tmp'},capture_output=True,timeout=20)
expected=Path('/mnt/lfs/usr/lib/gtk-3.0/3.0.0/immodules.cache').read_bytes()
assert query.returncode==0 and not query.stderr and query.stdout!=expected
before=b'# Created by gtk-query-immodules-3.0 from gtk+-3.24.52\n';after=b'# Created by /usr/bin/gtk-query-immodules-3.0 from gtk+-3.24.52\n'
assert query.stdout.count(before)==1 and query.stdout.replace(before,after)==expected
Path('/var/log/toddy/phase2/gtk3-ibus-cache-verify-2.json').write_text(json.dumps({'scope':'Read-only diagnosis/verification after successful native install: original invocation differs solely in GTK documented argv0 comment; every registration byte and all1882owned payload entries/archive unchanged. No install/cache/query generation replay.','original_query_exit':query.returncode,'original_query_stderr_empty':True,'only_difference_argv0_header':True,'owned_payload_entries_verified':len(r['payload']),'archive_sha256':r['archive_sha256'],'cache_sha256':hashlib.sha256(expected).hexdigest()},indent=2)+'\n')
PY
