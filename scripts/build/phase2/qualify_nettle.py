"""Require original crypto suite and own Nettle4 API correction without replay."""
from pathlib import Path
import hashlib,json,re
def digest(p):
 with p.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
def qualify(root):
 source=Path('/mnt/lfs/sources/phase2/inputs/nettle-4.0');work=Path('/mnt/lfs/sources/phase2/work/nettle-1');log=Path('/var/log/toddy/phase2')
 assert (source/'toddy-build.sh').read_bytes()==(root/'scripts/build/phase2/nettle-build.sh').read_bytes()
 assert digest(source/'toddy-probe.c')=='c0cc6d4b5426d8d279dcf6c8fab7e58dcf344dd7e7c0c06687ce348a1d69e1be'
 assert (log/'nettle-1.exit').read_text().strip()=='1' and (log/'nettle-consumer-2.exit').read_text().strip()=='0'
 assert json.loads((log/'nettle-1.job.json').read_text())['command'][2:]==[str(source),str(work),'bash','/src/toddy-build.sh']
 assert json.loads((log/'nettle-consumer-2.job.json').read_text())['command'][2:]==[str(source),str(work),'python3','-c',(root/'scripts/build/phase2/nettle_consumer.py').read_text(),(root/'scripts/build/phase2/nettle-probe.c').read_text()]
 result=json.loads((work/'stage-results.json').read_text());assert result['compile_exit']==result['stage_exit']==0 and result['original_ELFs_unchanged'] and result['stage_unchanged']
 text=(work/'original-tests.log').read_text();tests=[{'name':m[2],'result':m[1]} for m in re.finditer(r'^(PASS|SKIP|FAIL): (.+)$',text,re.M)]
 assert result['original_tests']==tests and sum(r['result']=='PASS' for r in tests)==122 and [r for r in tests if r['result']!='PASS']==[{'name':'x86-ibt','result':'SKIP'}]
 assert 'tests failed' not in text and len(re.findall(r'^All \d+ tests passed$',text,re.M))==3
 assert result['consumer_source_sha256']==digest(root/'scripts/build/phase2/nettle-probe.c')==digest(work/'native-probe-2.c') and result['consumer_binary_sha256']==digest(work/'native-probe-2')
 assert result['consumer']=={'SHA256_known_answer':True,'Hogweed_P256_generator_known_answer':True,'zero_scalar_and_off_curve_point_refused':True,'post_refusal_recovery':True,'lifecycle_cycles':2}
 for base,key in [('compile','artifacts'),('stage','stage_sha256')]:
  for name,sha in result[key].items():assert digest(work/base/name)==sha
 return result
