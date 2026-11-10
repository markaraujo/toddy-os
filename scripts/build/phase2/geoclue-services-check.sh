#!/bin/bash
set -euo pipefail
python3 - <<'PY'
from pathlib import Path
import hashlib,json
r=json.loads(Path('/var/log/toddy/phase2/geoclue-installed-services-3.json').read_text());assert r['daemon_uid']==30 and r['client_uid']==101 and r['external_routes']==0
assert r['actual_owned_bus_policy_used'] and not r['production_config_mutated'] and r['private_profile_removed']
assert hashlib.sha256(Path('/mnt/lfs/etc/geoclue/geoclue.conf').read_bytes()).hexdigest()==r['production_config_before_sha256']
assert len(r['records'])==2 and r['records'][0]['bus_guid']!=r['records'][1]['bus_guid']
for q in r['records']:
 for key in ['synthetic_static_coordinates_match','missing_DesktopId_refused','config_denial_enforced','cross_peer_property_refused','service_name_ownership_refused','agent_revoke_stops_client','agent_restore_recovers_client','explicit_Stop_inactive']:assert q[key],key
assert all(q['per_app_agent_authorization'].startswith('not exercised:') and q['agent_fixture_requests']==[] for q in r['records'])
assert not Path('/mnt/lfs/tmp/toddy-geoclue-services-3').exists()
PY
