"""Require the actual pinned generated data, source validity and typed invariants."""
from pathlib import Path
import hashlib,json
def digest(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def qualify(root):
 s=Path('/mnt/lfs/sources/phase2/inputs/gweather-locations-2026.2');w=Path('/mnt/lfs/sources/phase2/work/gweather-locations-1');l=Path('/var/log/toddy/phase2')
 for a,b in [('toddy-build.sh','gweather-locations-build.sh'),('toddy-probe.py','gweather-locations-probe.py')]:assert (s/a).read_bytes()==(root/'scripts/build/phase2'/b).read_bytes()
 assert (l/'gweather-locations-1.exit').read_text().strip()=='0'
 assert json.loads((l/'gweather-locations-1.job.json').read_text())['command']==['/bin/bash',str(root/'scripts/build/phase2/isolated.sh'),str(s),str(w),'bash','/src/toddy-build.sh']
 r=json.loads((w/'stage-results.json').read_text());assert r['compile_exit']==r['stage_exit']==0
 original=[json.loads(t) for t in (w/'compile/meson-logs/testlog.json').read_text().splitlines() if t.strip()]
 assert len(original)==1 and original[0]['name']=='lint - gweather-locations:Valid Locations file'
 assert original[0]['result']=='OK' and original[0]['returncode']==0
 assert r['original_tests']==[{k:t[k] for k in ['name','result','returncode']} for t in original]
 c=r['consumer'];assert c['normal_form'] and c['native_byteorder']=='little'
 assert (c['locations'],c['countries'],c['timezones'])==(8862,245,332)
 assert c['all_index_bounds_and_parent_links'] and c['country_BR_PT_lookup'] and c['timezone_Sao_Paulo_lookup'] and not c['real_owner_location_or_forecast_tested']
 assert c['data_sha256']==digest(w/'stage/usr/lib/gweather-locations/Locations.bin')
 assert c['source_XML_sha256']==r['source_XML_sha256']==digest(s/'data/Locations.xml')==digest(w/'stage/usr/share/gweather-locations/Locations.xml')
 for name,sha in r['stage_sha256'].items():assert digest(w/'stage'/name)==sha
 return r
