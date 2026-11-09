"""Qualify exact source/book install corrections and selected runtime originals."""
from pathlib import Path
import hashlib,json
def digest(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def qualify(root):
 source=Path('/mnt/lfs/sources/phase2/inputs/nspr-4.40');work=Path('/mnt/lfs/sources/phase2/work/nspr-1');log=Path('/var/log/toddy/phase2')
 for a,b in [('toddy-build.sh','nspr-build.sh'),('toddy-probe.c','nspr-probe.c')]:assert (source/a).read_bytes()==(root/'scripts/build/phase2'/b).read_bytes()
 prepared=json.loads((source/'toddy-prepared.json').read_text());assert {r['path'] for r in prepared['source_patches']}=={'nspr/pr/src/misc/Makefile.in','nspr/config/rules.mk'}
 for row in prepared['source_patches']:assert digest(source/row['path'])==row['after_sha256']
 assert (log/'nspr-1.exit').read_text().strip()=='0'
 assert json.loads((log/'nspr-1.job.json').read_text())['command'][2:]==[str(source),str(work),'bash','/src/toddy-build.sh']
 result=json.loads((work/'stage-results.json').read_text());assert result['compile_exit']==result['stage_exit']==0
 assert result['original_tests']==[{'name':name,'exit':0} for name in ['atomic','prftest','vercheck']]
 for row in result['original_tests']:
  text=(work/('original-'+row['name']+'.log')).read_text();assert ('PASS' in text if row['name']!='prftest' else 'test 2 passed' in text) and 'FAILED' not in text
 assert result['consumer']=={'version_compatibility_and_refusal':True,'real_joinable_threads_locked_updates':1000,'private_file_roundtrip_and_missing_file_refusal':True,'recovery_cycles':2} and not (work/'private-native-file').exists()
 assert not any(name.endswith('.a') for name in result['stage_sha256'])
 for base,key in [('compile','artifacts'),('stage','stage_sha256')]:
  for name,sha in result[key].items():assert digest(work/base/name)==sha
 return result
