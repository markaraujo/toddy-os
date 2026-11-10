"""Qualify the actual isolated NetworkManager build, not graphical integration."""
from pathlib import Path
import hashlib,json,re

def qualify(root):
 s=Path('/mnt/lfs/sources/phase2/inputs/NetworkManager-1.58.1');w=Path('/mnt/lfs/sources/phase2/work/networkmanager-1');l=Path('/var/log/toddy/phase2')
 for a,b in [('toddy-build.sh','networkmanager-build.sh'),('toddy-probe.c','networkmanager-probe.c')]:assert (s/a).read_bytes()==(root/'scripts/build/phase2'/b).read_bytes()
 assert (l/'networkmanager-1.exit').read_text().strip()=='0'
 assert json.loads((l/'networkmanager-1.job.json').read_text())['command']==['/bin/bash',str(root/'scripts/build/phase2/isolated.sh'),str(s),str(w),'bash','/src/toddy-build.sh']
 r=json.loads((w/'stage-results.json').read_text());assert r['compile_exit']==r['stage_exit']==0
 rows=[json.loads(x) for x in (w/'compile/meson-logs/testlog.json').read_text().splitlines() if x.strip()]
 assert len(rows)==67 and all(q['result']=='OK' and q['returncode']==0 for q in rows)
 assert r['original_tests']==[{k:q[k] for k in ['name','result','returncode']} for q in rows]
 assert len([s for q in rows for s in q.get('stdout','').splitlines() if re.search(r'^(?:ok|not ok).*#\s*SKIP',s,re.I)])==20
 assert r['consumer']=={'typed_UTF8_connection_roundtrip':True,'invalid_address_refused':True,'recovery_cycles':2,'actual_daemon_or_network_tested':False}
 assert len(r['artifacts'])==613 and len(r['stage_sha256'])==285
 for base,key in [('compile','artifacts'),('stage','stage_sha256')]:
  for name,sha in r[key].items():
   with (w/base/name).open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==sha
 return r
