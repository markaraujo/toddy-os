"""Bind exact standalone patch, original crypto programs and unchanged stage."""
from pathlib import Path
import hashlib,json,xml.etree.ElementTree as ET
def digest(p):
 with p.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
def qualify(root):
 source=Path('/mnt/lfs/sources/phase2/inputs/nss-3.126');work=Path('/mnt/lfs/sources/phase2/work/nss-1');log=Path('/var/log/toddy/phase2')
 patch=json.loads((root/'config/phase2/nss-patches.lock.json').read_text());assert digest(root/patch['patch_file'])==patch['patch_sha256'] and digest(Path('/mnt/lfs/sources/nss-standalone-1.patch'))==patch['official_patch_sha256']
 receipt=json.loads((log/'nss-input-reconcile-1.json').read_text());assert receipt['state']=='complete' and receipt['patch']==patch and receipt['original_regular_files']==4845 and receipt['only_reconciled_source_path']=='nss/manifest.mn'
 assert digest(source/'toddy-prepared.json')==receipt['prepared_sha256']
 for name,sha in patch['expected_changed_files'].items():assert digest(source/name)==sha
 for a,b in [('toddy-build.sh','nss-build.sh'),('toddy-probe.c','nss-probe.c')]:assert (source/a).read_bytes()==(root/'scripts/build/phase2'/b).read_bytes()
 assert (log/'nss-1.exit').read_text().strip()=='0'
 assert json.loads((log/'nss-1.job.json').read_text())['command'][2:]==[str(source),str(work),'bash','/src/toddy-build.sh']
 result=json.loads((work/'stage-results.json').read_text());assert result['compile_exit']==result['stage_exit']==0
 names=['base_gtest','der_gtest','cryptohi_gtest','freebl_gtest','util_gtest'];assert [r['name'] for r in result['original_tests']]==names
 total=0
 for row in result['original_tests']:
  cases=ET.parse(work/(row['name']+'.xml')).findall('.//testcase');assert row['exit']==0 and not row['failures'] and cases
  assert not any(c.find('failure') is not None or c.find('error') is not None for c in cases)
  passed=[c for c in cases if c.find('skipped') is None and c.get('status')=='run'];skipped=[c.get('classname')+'.'+c.get('name') for c in cases if c.find('skipped') is not None or c.get('status')!='run']
  assert row['passed']==len(passed) and row['skipped']==skipped;total+=len(passed)
 assert total==2271 and sum(len(r['skipped']) for r in result['original_tests'])==3
 assert result['consumer']=={'SHA256_known_answer':True,'native_random_bytes':True,'AES_GCM_roundtrip':True,'tampered_tag_refused':True,'post_refusal_recovery':True,'init_shutdown_cycles':2,'real_credentials_used':False}
 for base,key in [('source','artifacts'),('stage','stage_sha256')]:
  for name,sha in result[key].items():assert digest(work/base/name)==sha
 assert len(result['artifacts'])==745
 return result
