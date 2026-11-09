"""Require original Unicode programs and correct validation-before-normalization API."""
from pathlib import Path
import hashlib,json,re
def digest(p):
 with p.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
def qualify(root):
 source=Path('/mnt/lfs/sources/phase2/inputs/libunistring-1.4.2');work=Path('/mnt/lfs/sources/phase2/work/libunistring-1');log=Path('/var/log/toddy/phase2')
 assert (source/'toddy-build.sh').read_bytes()==(root/'scripts/build/phase2/libunistring-build.sh').read_bytes()
 assert digest(source/'toddy-probe.c')=='07d3714c14afe7b6affc830025366b7a6aded2c06cd896b66e9ecd2e08ddb1a9'
 assert (log/'libunistring-1.exit').read_text().strip()=='134' and (log/'libunistring-consumer-2.exit').read_text().strip()=='0'
 assert json.loads((log/'libunistring-1.job.json').read_text())['command'][2:]==[str(source),str(work),'bash','/src/toddy-build.sh']
 assert json.loads((log/'libunistring-consumer-2.job.json').read_text())['command'][2:]==[str(source),str(work),'python3','-c',(root/'scripts/build/phase2/libunistring_consumer.py').read_text(),(root/'scripts/build/phase2/libunistring-probe.c').read_text()]
 result=json.loads((work/'stage-results.json').read_text());assert result['compile_exit']==result['stage_exit']==0 and result['original_ELFs_unchanged'] and result['stage_unchanged']
 tests=[]
 for f in (work/'compile').rglob('*.trs'):
  m=re.search(r'^:test-result: (\S+)$',f.read_text(),re.M);assert m and m[1] in ['PASS','SKIP'];tests.append({'name':str(f.relative_to(work/'compile')),'result':m[1]})
 assert result['original_tests']==tests and len(tests)==674 and sum(r['result']=='PASS' for r in tests)==638
 assert result['consumer_source_sha256']==digest(root/'scripts/build/phase2/libunistring-probe.c')==digest(work/'native-probe-2.c') and result['consumer_binary_sha256']==digest(work/'native-probe-2')
 assert result['consumer']=={'UTF8_validation':True,'NFC_combining_mark_roundtrip':True,'Portuguese_lowercase':True,'overlong_UTF8_refused':True,'prior_state_preserved':True,'lifecycle_cycles':2}
 for base,key in [('compile','artifacts'),('stage','stage_sha256')]:
  for name,sha in result[key].items():assert digest(work/base/name)==sha
 return result
