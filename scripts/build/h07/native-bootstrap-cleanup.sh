#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
[[ -f /var/log/toddy/build/h07-dpkg.success.json ]]
python3 - <<'PY'
from datetime import datetime,timezone
from pathlib import Path
import hashlib,json,os
root=Path('/mnt/lfs');plan=json.loads(Path('/opt/toddy-build/config/native-bootstrap-cleanup.json').read_text())
owners=set()
for listing in (root/'var/lib/dpkg/info').glob('*.list'):
 owners.update(listing.read_text().splitlines())
paths=plan['paths'];assert len(paths)==len(set(paths))
rows=[]
for virtual in paths:
 assert virtual.startswith('/usr/') and '..' not in Path(virtual).parts
 assert virtual not in owners,('Now owned; re-audit before cleanup',virtual)
 path=root/virtual.lstrip('/')
 assert path.is_file() or path.is_symlink(),('Absent/changed; inspect checkpoint',virtual)
 row={'path':virtual,'mode':path.lstat().st_mode}
 if path.is_symlink():row['symlink']=os.readlink(path)
 else:
  with path.open('rb') as stream:row['sha256']=hashlib.file_digest(stream,'sha256').hexdigest()
 rows.append(row)
destination=root/'sources/recovery'/('native-bootstrap-cleanup-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ'))
destination.mkdir()
(destination/'manifest.json').write_text(json.dumps({'complete':False,'entries':rows},indent=2)+'\n')
for row in rows:
 path=root/row['path'].lstrip('/');target=destination/row['path'].lstrip('/')
 target.parent.mkdir(parents=True,exist_ok=True);path.rename(target)
(destination/'manifest.json').write_text(json.dumps({'complete':True,'entries':rows},indent=2)+'\n')
Path('/var/log/toddy/native-bootstrap-cleanup.json').write_text(json.dumps({'quarantine':str(destination),'entries':len(rows),'complete':True},indent=2)+'\n')
print('Quarantined exact unowned bootstrap remnants:',len(rows))
PY
