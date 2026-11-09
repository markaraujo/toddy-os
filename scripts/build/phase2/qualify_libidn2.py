"""Require original IDNA programs and actual Unicode/nontransitional refusals."""
from pathlib import Path
import hashlib,json,re
def digest(p):
 with p.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
def qualify(root):
 source=Path('/mnt/lfs/sources/phase2/inputs/libidn2-2.3.8');work=Path('/mnt/lfs/sources/phase2/work/libidn2-1');log=Path('/var/log/toddy/phase2')
 for a,b in [('toddy-build.sh','libidn2-build.sh'),('toddy-probe.c','libidn2-probe.c')]:assert (source/a).read_bytes()==(root/'scripts/build/phase2'/b).read_bytes()
 assert (log/'libidn2-1.exit').read_text().strip()=='0'
 assert json.loads((log/'libidn2-1.job.json').read_text())['command'][2:]==[str(source),str(work),'bash','/src/toddy-build.sh']
 result=json.loads((work/'stage-results.json').read_text());assert result['compile_exit']==result['stage_exit']==0
 tests=[]
 for f in (work/'compile').rglob('*.trs'):
  m=re.search(r'^:test-result: (\S+)$',f.read_text(),re.M);assert m and m[1]=='PASS';tests.append({'name':str(f.relative_to(work/'compile')),'result':'PASS'})
 assert result['original_tests']==tests and len(tests)==15
 assert result['consumer']=={'UTF8_punycode_roundtrip':True,'nontransitional_sharp_s':True,'invalid_UTF8_and_leading_hyphen_refused':True,'post_refusal_recovery':True,'cycles':2}
 for base,key in [('compile','artifacts'),('stage','stage_sha256')]:
  for name,sha in result[key].items():assert digest(work/base/name)==sha
 return result
