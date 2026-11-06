#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
python3 - <<'PY'
from pathlib import Path
import hashlib,json,stat
root=Path('/opt/toddy-build');base=Path('/mnt/lfs/sources/test-inputs/vim-glvs')
assert (base/'manifest.json').read_bytes()==(root/'config/vim-glvs-inputs.lock.json').read_bytes()
assert (base/'bin/curl').read_bytes()==(root/'scripts/build/h07/verified-vim-curl.py').read_bytes()
rows=json.loads((base/'manifest.json').read_text())['components']
for row in rows:
 path=base/'payloads'/row['filename']
 assert not path.is_symlink() and path.stat().st_uid==0 and not (path.stat().st_mode & 0o222)
 assert hashlib.sha256(path.read_bytes()).hexdigest()==row['sha256']
events=[json.loads(l) for l in Path('/mnt/lfs/sources/evidence/h07-vim-glvs-inputs/download-events.jsonl').read_text().splitlines()]
assert {(r['kind'],r['source_id']) for r in events}=={(kind,row['source_id']) for row in rows for kind in ['metadata','plugin']}
assert all(r['verified'] and r['uid']!=0 for r in events)
print('Protected input cache and actual verification events passed; no Vim test executed yet')
PY
