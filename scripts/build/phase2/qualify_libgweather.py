"""Qualify offline core while preserving the real external METAR failure."""
from pathlib import Path
import hashlib,json,re
def digest(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def qualify(root):
 s=Path('/mnt/lfs/sources/phase2/inputs/libgweather-4.6.0');w=Path('/mnt/lfs/sources/phase2/work/libgweather-1');l=Path('/var/log/toddy/phase2')
 assert digest(s/'toddy-build.sh')=='71f55fd5ab35c1b8dc07edb1b554bb8c76a0af40f0ac8d008b54086e6241bee1'
 assert (s/'toddy-probe.c').read_bytes()==(root/'scripts/build/phase2/libgweather-probe.c').read_bytes()
 body=(root/'scripts/build/phase2/libgweather-build.sh').read_text();prefix=['/bin/bash',str(root/'scripts/build/phase2/isolated.sh'),str(s),str(w)]
 assert (l/'libgweather-1.exit').read_text().strip()=='1' and (l/'libgweather-stage-2.exit').read_text().strip()=='0'
 assert json.loads((l/'libgweather-1.job.json').read_text())['command']==prefix+['bash','/src/toddy-build.sh']
 assert json.loads((l/'libgweather-stage-2.job.json').read_text())['command']==prefix+['python3','-c',(root/'scripts/build/phase2/libgweather_finish.py').read_text(),body]
 assert (s/'toddy-build.sh').read_text().split("python3 - <<'PY'")[0].replace('test_libgweather duplicates timezones metar >','test_libgweather duplicates timezones >')==body.split("python3 - <<'PY'")[0]
 r=json.loads((w/'stage-results.json').read_text());assert r['compile_exit']==r['stage_exit']==0 and r['selected_core_programs']==3 and not r['external_METAR_qualified']
 tests=[json.loads(t) for t in (w/'compile/meson-logs/testlog.json').read_text().splitlines() if t.strip()]
 assert len(tests)==4
 core=[t for t in tests if t['name']!='libgweather:metar'];external=[t for t in tests if t['name']=='libgweather:metar']
 assert {t['name'] for t in core}=={'libgweather:test_libgweather','libgweather:duplicates','libgweather:timezones'} and all(t['result']=='OK' and t['returncode']==0 for t in core)
 assert sum(len(re.findall(r'^ok \d+ ',t['stdout'],re.M)) for t in core)==12
 assert len(external)==1 and external[0]['result']=='ERROR' and external[0]['returncode']==-6
 assert 'aviationweather.gov' in (w/'original-tests.log').read_text() and 'Name or service not known' in (w/'original-tests.log').read_text()
 assert r['original_tests']==[{k:t[k] for k in ['name','result','returncode']}|{'nested_skip_lines':[line for line in t.get('stdout','').splitlines() if re.search(r'#\s*SKIP',line,re.I)]} for t in tests]
 assert r['consumer']=={'country_BR_PT_lookup':True,'SBGR_LPPT_station_lookup':True,'coordinates_match_owned_database':True,'location_variant_roundtrip':True,'wrong_variant_type_refused':True,'post_refusal_cycles':2,'remote_forecast_or_owner_position_tested':False}
 before=json.loads((w/'ELFs-before-stage-2.json').read_text());assert len(before)==42 and before==r['artifacts']
 for base,key in [('compile','artifacts'),('stage','stage_sha256')]:
  for name,sha in r[key].items():assert digest(w/base/name)==sha
 return r
