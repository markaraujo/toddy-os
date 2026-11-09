"""Require original ASN.1 suite and source-bound strict DER/refusal/recovery."""
import hashlib,json,re
from pathlib import Path
def digest(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def qualify(root):
 source=Path('/mnt/lfs/sources/phase2/inputs/libtasn1-4.21.0');work=Path('/mnt/lfs/sources/phase2/work/libtasn1-1');log=Path('/var/log/toddy/phase2')
 for a,b in [('toddy-build.sh','libtasn1-build.sh'),('toddy-probe.c','libtasn1-probe.c')]:assert (source/a).read_bytes()==(root/'scripts/build/phase2'/b).read_bytes()
 assert (log/'libtasn1-1.exit').read_text().strip()=='0'
 assert json.loads((log/'libtasn1-1.job.json').read_text())['command'][2:]==[str(source),str(work),'bash','/src/toddy-build.sh']
 result=json.loads((work/'stage-results.json').read_text());assert result['compile_exit']==result['stage_exit']==0
 tests=[]
 for path in (work/'compile').rglob('*.trs'):
  match=re.search(r'^:test-result: (\S+)$',path.read_text(),re.M);assert match and match[1]=='PASS';tests.append({'name':str(path.relative_to(work/'compile')),'result':'PASS'})
 assert len(tests)==40 and tests==result['original_tests']
 consumer=result['consumer'];assert consumer=={'version':'4.21.0','strict_DER_typed_roundtrip':True,'truncated_input_refused':True,'recovery_cycles':2}
 for base,key in [('compile','artifacts'),('stage','stage_sha256')]:
  for name,sha in result[key].items():assert digest(work/base/name)==sha
 return result
