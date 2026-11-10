"""Bind selected portable originals and actual source-built geocode C ABI."""
from pathlib import Path
import hashlib,json,re
def digest(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def qualify(root):
 s=Path('/mnt/lfs/sources/phase2/inputs/geocode-glib-3.26.4');w=Path('/mnt/lfs/sources/phase2/work/geocode-glib-1');l=Path('/var/log/toddy/phase2')
 for a,b in [('toddy-build.sh','geocode-glib-build.sh'),('toddy-probe.c','geocode-glib-probe.c')]:assert (s/a).read_bytes()==(root/'scripts/build/phase2'/b).read_bytes()
 assert (l/'geocode-glib-1.exit').read_text().strip()=='0'
 assert json.loads((l/'geocode-glib-1.job.json').read_text())['command']==['/bin/bash',str(root/'scripts/build/phase2/isolated.sh'),str(s),str(w),'bash','/src/toddy-build.sh']
 r=json.loads((w/'stage-results.json').read_text());assert r['compile_exit']==r['stage_exit']==0
 tests=[json.loads(t) for t in (w/'compile/meson-logs/testlog.json').read_text().splitlines() if t.strip()]
 assert len(tests)==2 and {t['name'] for t in tests}=={'geocode-glib:Geo URI','geocode-glib:Test mock backend'}
 assert all(t['result']=='OK' and t['returncode']==0 for t in tests)
 assert r['original_tests']==[{k:t[k] for k in ['name','result','returncode']} for t in tests]
 api=(w/'original-portable-API.log').read_text();assert len(re.findall(r'^ok \d+ ',api,re.M))==3 and not re.search(r'^not ok',api,re.M)
 assert r['original_API_paths']==['/geocode/distance','/geocode/zero_distance','/geocode/osm_type'] and r['original_API_passes']==3
 assert all(re.search(r'^ok \d+ '+re.escape(name)+r'$',api,re.M) for name in r['original_API_paths'])
 assert r['consumer']=={'UTF8_location_description':True,'geo_URI_roundtrip':True,'malformed_URI_refused':True,'post_refusal_recovery_cycles':2,'remote_geocoding_tested':False}
 for base,key in [('compile','artifacts'),('stage','stage_sha256')]:
  for name,sha in r[key].items():assert digest(w/base/name)==sha
 return r
