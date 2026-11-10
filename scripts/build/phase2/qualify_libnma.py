"""Bind original libnma compilation and stage-only recovery, with scoped GI proof."""
from pathlib import Path
import hashlib,json

def qualify(root):
 s=Path('/mnt/lfs/sources/phase2/inputs/libnma-1.10.6');w=Path('/mnt/lfs/sources/phase2/work/libnma-1');l=Path('/var/log/toddy/phase2')
 for a,b in [('toddy-build.sh','libnma-build.sh'),('toddy-probe.c','libnma-probe.c')]:assert (s/a).read_bytes()==(root/'scripts/build/phase2'/b).read_bytes()
 assert (l/'libnma-1.exit').read_text().strip()=='1' and (l/'libnma-stage-2.exit').read_text().strip()=='0'
 command=json.loads((l/'libnma-stage-2.job.json').read_text())['command'];assert command==['/bin/bash',str(root/'scripts/build/phase2/isolated.sh'),str(s),str(w),'bash','-c',(root/'scripts/build/phase2/libnma-stage-2.sh').read_text()]
 r=json.loads((w/'stage-results.json').read_text());assert r['compile_exit']==r['stage_exit']==0
 assert r['original_tests']==[{'name':'libnma:test-utils','result':'OK','returncode':0}]
 assert len(r['original_registered_tests'])==1 and r['original_registered_tests'][0]['name']=='test-utils'
 assert len(r['artifacts'])==101 and len(r['stage_sha256'])==114 and r['unchanged_original_elfs']==r['artifacts']
 for major in [3,4]:
  assert r['consumers'][str(major)]=={'GTK_major':major,'libnma_version':'1.10.6','actual_widget_types':True,'libnm_refusal_recovery':True,'widget_open_or_focus_tested':False}
  q=json.loads((w/('native-GI-'+str(major)+'.json')).read_text());assert q['GTK_major']==major and q['public_widget_and_mobile_types'] and not q['actual_widget_open_tested']
 assert '#define WITH_GCR 1' in (w/'compile/config.h').read_text()
 for base,key in [('compile','artifacts'),('stage','stage_sha256')]:
  for name,sha in r[key].items():
   with (w/base/name).open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==sha
 return r
