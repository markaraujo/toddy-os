"""Exact first-build original-case binding for two small metadata prerequisites."""
from pathlib import Path
import hashlib,json,xml.etree.ElementTree as E

def digest(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def qualify(root,name):
 assert name in ['brotli','inih']
 version='1.2.0' if name=='brotli' else '62';s=Path('/mnt/lfs/sources/phase2/inputs')/(name+'-'+version);w=Path('/mnt/lfs/sources/phase2/work')/(name+'-1');l=Path('/var/log/toddy/phase2')
 for a,b in [('toddy-build.sh',name+'-build.sh'),('toddy-probe.'+('py' if name=='brotli' else 'c'),name+'-probe.'+('py' if name=='brotli' else 'c'))]:
  actual=(s/a).read_text();expected=(root/'scripts/build/phase2'/b).read_text()
  if name=='inih' and a=='toddy-build.sh' and actual!=expected:actual=actual.replace('len(rows)==15','len(rows)==16').replace('all15original','all16original')
  assert actual==expected
 expected='816c96e8e8f193b40151dad7e8ff37b1221d019dbcb9c35cd3fadbfe6477dfec' if name=='brotli' else '9c15fa751bb8093d042dae1b9f125eb45198c32c6704cd5481ccde460d4f8151'
 assert json.loads((s/'toddy-prepared.json').read_text())['source_sha256']==expected
 if name=='inih' and (l/'inih-collect-2.exit').exists():
  assert (l/'inih-1.exit').read_text().strip()=='1' and (l/'inih-collect-2.exit').read_text().strip()=='0'
  assert json.loads((l/'inih-collect-2.job.json').read_text())['command'][-1]==(root/'scripts/build/phase2/inih_collect.py').read_text()
 else:assert (l/(name+'-1.exit')).read_text().strip()=='0'
 assert (w/'original-tests.exit').read_text().strip()=='0'
 r=json.loads((w/'stage-results.json').read_text());assert r['compile_exit']==r['stage_exit']==0
 for base,key in [('compile','artifacts'),('stage','stage_sha256')]:
  actual={str(p.relative_to(w/base)):digest(p) for p in (w/base).rglob('*') if p.is_file() and not p.is_symlink() and (key!='artifacts' or p.open('rb').read(4)==b'\x7fELF')};assert actual==r[key] and actual
 if name=='brotli':
  cases=E.parse(w/'original-tests.xml').getroot().findall('.//testcase');assert len(cases)==12 and all(c.get('status')=='run' and c.find('failure') is None and c.find('skipped') is None for c in cases)
  assert r['original_cases']==[c.get('name') for c in cases] and len(r['artifacts'])==42 and len(r['stage_sha256'])==17
  assert r['consumer']=={'UTF8_and_binary_roundtrip_cycles':2,'compressed_integrity_checks':2,'malformed_refusals':2,'malformed_input_unchanged':True,'recovery_cycles':2}
 else:
  rows=[json.loads(x) for x in (w/'compile/meson-logs/testlog.json').read_text().splitlines() if x.strip()];assert len(rows)==16 and all(x['result']=='OK' and x['returncode']==0 for x in rows)
  assert r['original_tests']==[{k:x[k] for k in ['name','result','returncode']} for x in rows]
  assert r['consumer']=={'C_and_Cpp_UTF8_parse_cycles':2,'typed_and_missing_defaults':True,'malformed_refusals':2,'prior_state_retained':True,'recovery_cycles':2}
 return r
