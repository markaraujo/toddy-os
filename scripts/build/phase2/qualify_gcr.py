"""Require source-bound original Gcr outcomes and exact private fixture isolation."""
import hashlib,json,re
from pathlib import Path
def digest(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def qualify(root):
 source=Path('/mnt/lfs/sources/phase2/inputs/gcr-4.4.0.1');work=Path('/mnt/lfs/sources/phase2/work/gcr-1');log=Path('/var/log/toddy/phase2')
 assert digest(source/'toddy-build.sh')=='ddf5220f04a57f3f0abca182bda4519154c7d2bee995e844e854bf4a18153ee5'
 assert digest(source/'toddy-probe.c')=='2889245765d3dad60c1d6826f4cf440e800d3f1ec5119a2c42a344d611ef7ef9'
 assert (log/'gcr-1.exit').read_text().strip()=='1'
 assert json.loads((log/'gcr-1.job.json').read_text())['command'][2:]==[str(source),str(work),'dbus-run-session','--','bash','/src/toddy-build.sh']
 for job,script,cmd in [('gcr-askpass-2','gcr_askpass_repair.py',['dbus-run-session','--','python3','-c']),('gcr-askpass-cases-3','gcr_askpass_cases.py',['dbus-run-session','--','python3','-c']),('gcr-finish-4','gcr_finish.py',['python3','-c'])]:
  assert (log/(job+'.exit')).read_text().strip()=='0';command=[str(source),str(work),*cmd,(root/'scripts/build/phase2'/script).read_text()]
  if job=='gcr-finish-4':command.append((root/'scripts/build/phase2/gcr-probe.c').read_text())
  assert json.loads((log/(job+'.job.json')).read_text())['command'][2:]==command
 result=json.loads((work/'stage-results.json').read_text());assert result['compile_exit']==result['stage_exit']==0 and result['reused_original_programs']==38 and result['original_nested_skips']==[]
 initial=[json.loads(s) for s in (work/'initial-testlog-1.json').read_text().splitlines() if s.strip()];passed=[r for r in initial if r['result']=='OK' and r['returncode']==0];assert len(initial)==39 and len(passed)==38
 assert result['original_tests']==[{k:r[k] for k in ['name','result','returncode']} for r in passed]
 partial=json.loads((work/'askpass-2.json').read_text());assert partial['exit']==0
 row=[json.loads(s) for s in (work/'compile/meson-logs/testlog.json').read_text().splitlines() if s.strip()];assert len(row)==1 and re.search(r'^ok \d+ /gcr/ssh-askpass/properties$',row[0]['stdout'],re.M)
 assert len(re.findall(r'^ok \d+.*# SKIP ssh-keygen not found$',row[0]['stdout'],re.M))==2,'Original missing-tool skips retained, never counted as passes'
 cases=json.loads((work/'askpass-cases-3.json').read_text());assert len(cases['runs'])==2 and all(r['exit']==0 and r['expected_outcome_passed'] for r in cases['runs'])
 for r in cases['runs']:
  for stream in ['stdout','stderr']:assert digest(work/('askpass-3-'+r['name']+'.'+stream))==r[stream+'_sha256']
  text=(work/('askpass-3-'+r['name']+'.stdout')).read_text();assert not re.search('SKIP|not ok',text,re.I) and re.search(r'^ok \d+ /gcr/ssh-askpass/'+r['name']+'$',text,re.M)
 assert result['repaired_original_askpass_cases']==[{'name':'properties','exit':0},*cases['runs']]
 accepted=json.loads((log/'gcr-askpass-prepare-1.json').read_text());assert accepted['state']=='complete'
 assert result['unchanged_original_elfs']==partial['unchanged_original_elfs']==cases['unchanged_original_elfs']==accepted['gcr_original_elfs']
 for name,sha in result['unchanged_original_elfs'].items():assert digest(work/'compile'/name)==sha
 sample='gcr/fixtures/pem-rsa-enc.key';sha='55b32dbd31618e5e949be919fb42ed7ca519f8e4ad5b352c9136ab7202e6ef4e'
 assert digest(source/sample)==digest(work/'source-fixtures/pem-rsa-enc.key')==cases['private_sample_sha256']==sha
 assert source.joinpath(sample).stat().st_mode&0o7777==accepted['source_sample_mode']==0o644
 assert (work/'source-fixtures/pem-rsa-enc.key').stat().st_mode&0o7777==0o600
 assert digest(work/'test-sdk/bin/ssh-keygen')==accepted['sdk_sha256']
 assert result['consumer']=={'libgcrypt_transport_roundtrip':True,'malformed_exchange_refused':True,'prior_state_preserved':True,'recovery_cycles':2,'real_credentials_used':False}
 assert result['gi']['native_gi_types']==['GcrSecretExchange','GckModule']
 for name,sha in result['stage_sha256'].items():assert digest(work/'stage'/name)==sha
 return result
