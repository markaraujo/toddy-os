"""Exact header SDK, private test source and original core CTest binding."""
from pathlib import Path
import hashlib,json,xml.etree.ElementTree as ET

def digest(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def qualify(root):
 s=Path('/mnt/lfs/sources/phase2/inputs/fast-float-8.2.10');w=Path('/mnt/lfs/sources/phase2/work/fast-float-1');l=Path('/var/log/toddy/phase2')
 for a,b in [('toddy-build.sh','fast-float-build.sh'),('toddy-probe.py','fast-float-probe.py')]:assert (s/a).read_bytes()==(root/'scripts/build/phase2'/b).read_bytes()
 p=json.loads((s/'toddy-prepared.json').read_text());assert p['source_sha256']=='76f958dd97b1cf4d8862d1f0986a47d4bdfa8845252bae15ef0f40de3b95961f'
 assert p['extra_source']['commit']=='dfb11445b941a75813c26aa9184f08c6ce774615' and p['extra_source']['sha256']=='a31178827d624e0e7c31419f61a3b526cadf2f744c82bc532be9773fd673e090'
 sdk={str(f.relative_to(s/'toddy-test-sdk')):digest(f) for f in (s/'toddy-test-sdk').rglob('*') if f.is_file() and not f.is_symlink()};assert sdk==p['private_test_sdk']['files'] and len(sdk)==270
 assert (l/'fast-float-1.exit').read_text().strip()=='0'
 assert json.loads((l/'fast-float-1.job.json').read_text())['command']==['/bin/bash',str(root/'scripts/build/phase2/isolated.sh'),str(s),str(w),'bash','/src/toddy-build.sh']
 r=json.loads((w/'stage-results.json').read_text());assert r['compile_exit']==r['stage_exit']==0
 cases=ET.parse(w/'original-tests.xml').getroot().findall('.//testcase');assert len(cases)==14 and not any(c.find(k) is not None for c in cases for k in ['failure','error','skipped'])
 assert r['original_tests']==[{'name':c.get('name'),'status':c.get('status')} for c in cases]
 assert len(r['artifacts'])==47 and len(r['stage_sha256'])==12
 for base,key in [('tests','artifacts'),('stage','stage_sha256')]:
  for name,sha in r[key].items():assert digest(w/base/name)==sha
 assert not any('doctest' in name for name in r['stage_sha256'])
 assert r['consumer']=={'typed_float_double':True,'trailing_input_pointer':True,'invalid_input_refused':True,'overflow_refused':True,'reset_recovery_cycles':2,'CMake_discovered_version':'8.2.10','header_only_SDK':True,'terminal_or_GUI_tested':False}
 return r
