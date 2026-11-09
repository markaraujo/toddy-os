"""Qualify actual AccountsService fixture outcomes without claiming real accounts."""
import hashlib,json,re
from pathlib import Path

def digest(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def qualify(root):
 source=Path('/mnt/lfs/sources/phase2/inputs/accountsservice-26.27.3');work=Path('/mnt/lfs/sources/phase2/work/accountsservice-1');log=Path('/var/log/toddy/phase2')
 assert (source/'toddy-probe.py').read_bytes()==(root/'scripts/build/phase2/accountsservice-probe.py').read_bytes()
 result=json.loads((work/'stage-results.json').read_text());assert result['compile_exit']==result['stage_exit']==0 and result['source_version']=='26.27.3'
 if (log/'accountsservice-locale-5.exit').exists():
  assert digest(source/'toddy-build.sh')=='f662037aefc6d2e3f6bb23c434ad5ee34806f4dc9c1b262c3438242e4f87ddde'
  for job,script in [('accountsservice-json-c-2','accountsservice_resume.py'),('accountsservice-startup-3','accountsservice_diagnose.py'),('accountsservice-machine-id-4','accountsservice_machine_id.py'),('accountsservice-locale-5','accountsservice_locale.py')]:
   r=json.loads((log/(job+'.job.json')).read_text());assert r['command'][2:]==[str(source),str(work),'python3','-c',(root/'scripts/build/phase2'/script).read_text()]
  assert (log/'accountsservice-locale-5.exit').read_text().strip()=='0'
  rows=[json.loads(s) for s in (work/'initial-testlog-2.json').read_text().splitlines() if s.strip()]
  assert len(rows)==18 and sum(r['result']=='OK' and r['returncode']==0 for r in rows)==14
  repaired=json.loads((work/'machine-id-cases-4.json').read_text());assert len(repaired)==4 and sum(r['exit']==0 for r in repaired)==3
  last=json.loads((work/'locale-case-5.json').read_text());assert last['name']=='Tests.test_languages' and last['exit']==0 and re.search(r'Ran 1 test',last['stderr']) and '\nOK\n' in last['stderr']
  assert result['reused_original_programs']==14 and len(result['repaired_original_cases'])==4 and all(r['exit']==0 for r in result['repaired_original_cases'])
  for name,sha in result['unchanged_original_elfs'].items():assert digest(work/'compile'/name)==sha
 else:
  assert (log/'accountsservice-1.exit').read_text().strip()=='0'
  assert (source/'toddy-build.sh').read_bytes()==(root/'scripts/build/phase2/accountsservice-build.sh').read_bytes()
  assert result['selected_original_programs']>=18 and all(r['exit']==0 for r in result['original_tests'])
 consumer=result['consumer'];assert consumer['version']=='26.27.3' and consumer['daemon_version_exit']==0 and consumer['native_gi_types']==['ActUser','ActUserManager']
 for name,sha in result['stage_sha256'].items():assert digest(work/'stage'/name)==sha
 assert set(result['stage_sha256'])=={str(p.relative_to(work/'stage')) for p in (work/'stage').rglob('*') if p.is_file() and not p.is_symlink()}
 assert not any('mocklibc' in n for n in result['stage_sha256'])
 return result
