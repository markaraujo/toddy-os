"""Bind owned non-widget libhandy scope; keep all original display tests pending."""
from pathlib import Path
import hashlib,json

def digest(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def qualify(root):
 s=Path('/mnt/lfs/sources/phase2/inputs/libhandy-1.8.3');w=Path('/mnt/lfs/sources/phase2/work/libhandy-1');l=Path('/var/log/toddy/phase2')
 prep=json.loads((s/'toddy-prepared.json').read_text());assert prep['source_sha256']=='05b497229073ff557f10b326e074c5066f8743a302d4820ab97bcb5cd2dab087'
 r=json.loads((w/'stage-results.json').read_text());assert r['compile_exit']==r['stage_exit']==0 and r['original_tests_passed']==0
 rows=json.loads((w/'original-registered-tests.json').read_text());assert len(rows)==30 and r['original_graphical_tests_pending']==[x['name'] for x in rows]
 assert len(r['artifacts'])==122 and len(r['stage_sha256'])==78
 for base,key in [('compile','artifacts'),('stage','stage_sha256')]:
  for name,sha in r[key].items():assert digest(w/base/name)==sha
 if (l/'libhandy-gi-3.exit').exists():
  assert (l/'libhandy-1.exit').read_text().strip()=='134' and 'g_value_type_compatible' in (l/'libhandy-1.log').read_text()
  assert digest(s/'toddy-build.sh')==prep['recipe_sha256']=='3bb309db51b7d451388aa53acc8b5bbd30399777282f39c920c4c521d81dbd76'
  assert digest(s/'toddy-probe.c')=='d49bebd7db3ff0f42ebff1d882286f8996a045c697c85a55561c54eef07bcec9'
  assert (l/'libhandy-probe-2.exit').read_text().strip()=='1' and 'has no attribute' in (l/'libhandy-probe-2.log').read_text()
  assert (w/'probe-2/consumer.exit').read_text().strip()=='0'
  assert (l/'libhandy-gi-3.exit').read_text().strip()=='0'
  assert (w/'probe-2/probe.c').read_bytes()==(root/'scripts/build/phase2/libhandy-probe.c').read_bytes()
  gi=(root/'scripts/build/phase2/libhandy-gi-probe.py').read_text()
  assert (w/'GI-3/probe.py').read_text()==gi
  code=(root/'scripts/build/phase2/libhandy_gi_resume.py').read_text()+'\nmain('+repr(gi)+')\n'
  assert json.loads((l/'libhandy-gi-3.job.json').read_text())['command'][-3:]==['python3','-c',code]
  before=json.loads((w/'probe-2/before.json').read_text());assert all(r[k]==before[k] for k in ['artifacts','stage_sha256'])
  assert r['probe_only_recovery']['compile_and_stage_unchanged']
 else:
  assert (l/'libhandy-1.exit').read_text().strip()=='0'
  assert (s/'toddy-build.sh').read_bytes()==(root/'scripts/build/phase2/libhandy-build.sh').read_bytes()
  assert (s/'toddy-probe.c').read_bytes()==(root/'scripts/build/phase2/libhandy-probe.c').read_bytes()
 assert r['consumer']=={'header_version':'1.8.3','UTF8_value_copy_ownership':True,'take_dup_ownership':True,'navigation_enum':True,'reset_cycles':2,'widget_or_display_tested':False}
 assert r['GI_consumer']=={'namespace':'Handy1','UTF8_value_object':True,'widget_or_display_tested':False}
 return r
