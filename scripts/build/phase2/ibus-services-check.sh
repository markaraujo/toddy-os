#!/bin/bash
set -euo pipefail
python3 - <<'PY_CHECK'
from pathlib import Path
import json
r=json.loads(Path('/var/log/toddy/phase2/ibus-installed-services-4.json').read_text())
assert r['uid']==101 and r['network_interfaces']==['lo'] and r['external_routes']==0
assert r['private_process_cleanup_verified'] and r['private_profile_removed']
assert len(r['records'])==2 and all(t['exit']==0 for t in r['records'])
assert r['records'][0]['result']['bus_guid']!=r['records'][1]['result']['bus_guid']
for t in r['records']:
 q=t['result'];assert q['actual_installed_engine_commit']==['ã'] and q['precancelled_read_refused'] and q['post_cancel_engine_read_recovered'] and q['requested_Stop_exit']==0
assert not Path('/mnt/lfs/tmp/toddy-ibus-installed-services-4').exists()
PY_CHECK
