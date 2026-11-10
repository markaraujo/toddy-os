"""Bind fmt shared build/default originals/installed-layout CMake consumer."""
from pathlib import Path
import hashlib,json,xml.etree.ElementTree as ET

def digest(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def qualify(root):
 s=Path('/mnt/lfs/sources/phase2/inputs/fmt-12.2.0');w=Path('/mnt/lfs/sources/phase2/work/fmt-1');l=Path('/var/log/toddy/phase2')
 for a,b in [('toddy-build.sh','fmt-build.sh'),('toddy-probe.py','fmt-probe.py')]:assert (s/a).read_bytes()==(root/'scripts/build/phase2'/b).read_bytes()
 assert json.loads((s/'toddy-prepared.json').read_text())['source_sha256']=='8b852bb5aa6e7d8564f9e81394055395dd1d1936d38dfd3a17792a02bebd7af0'
 assert (l/'fmt-1.exit').read_text().strip()=='0'
 assert json.loads((l/'fmt-1.job.json').read_text())['command']==['/bin/bash',str(root/'scripts/build/phase2/isolated.sh'),str(s),str(w),'bash','/src/toddy-build.sh']
 r=json.loads((w/'stage-results.json').read_text());assert r['compile_exit']==r['stage_exit']==0
 cases=ET.parse(w/'original-tests.xml').getroot().findall('.//testcase');assert len(cases)==21 and not any(c.find(k) is not None for c in cases for k in ['failure','error','skipped'])
 assert not any('[  SKIPPED ]' in ''.join(c.itertext()) for c in cases)
 assert r['original_tests']==[{'name':c.get('name'),'status':c.get('status')} for c in cases]
 assert len(r['artifacts'])==78 and len(r['stage_sha256'])==22
 for base,key in [('compile','artifacts'),('stage','stage_sha256')]:
  for name,sha in r[key].items():assert digest(w/base/name)==sha
 assert not any('gtest' in name for name in r['stage_sha256'])
 assert r['consumer']=={'Unicode_decimal_hex':True,'runtime_format_error_refused':True,'reset_recovery_cycles':2,'CMake_discovered_version':'12.2.0','shared_library_consumer':True,'terminal_or_GUI_tested':False}
 return r
