"""Require original suffix/cookie/ICU corpus programs and native policy consumer."""
from pathlib import Path
import hashlib,json
def digest(p):
 with p.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
def qualify(root):
 source=Path('/mnt/lfs/sources/phase2/inputs/libpsl-0.23.3');work=Path('/mnt/lfs/sources/phase2/work/libpsl-1');log=Path('/var/log/toddy/phase2')
 assert digest(source/'toddy-build.sh')=='40f15079b011e485f738a57646309b7a3c4cc86c50d597c2e2a69df573e64312'
 assert (source/'toddy-probe.c').read_bytes()==(root/'scripts/build/phase2/libpsl-probe.c').read_bytes()
 assert (log/'libpsl-1.exit').read_text().strip()=='1' and (log/'libpsl-metadata-2.exit').read_text().strip()=='0'
 assert json.loads((log/'libpsl-1.job.json').read_text())['command'][2:]==[str(source),str(work),'bash','/src/toddy-build.sh']
 assert json.loads((log/'libpsl-metadata-2.job.json').read_text())['command'][2:]==[str(source),str(work),'python3','-c',(root/'scripts/build/phase2/libpsl_metadata.py').read_text()]
 result=json.loads((work/'stage-results.json').read_text());assert result['compile_exit']==result['stage_exit']==0 and result['metadata_only_reconciliation']
 rows=[json.loads(s) for s in (work/'compile/meson-logs/testlog.json').read_text().splitlines() if s.strip()];assert len(rows)==8 and all(r['result']=='OK' and r['returncode']==0 for r in rows)
 assert result['original_tests']==[{k:r[k] for k in ['name','result','returncode']} for r in rows]
 options={r['name']:r['value'] for r in json.loads((work/'compile/meson-info/intro-buildoptions.json').read_text())};assert options['runtime']=='libicu' and options['builtin'] is True
 assert result['consumer']=={'builtin_public_suffix_and_registrable_domain':True,'public_suffix_cookie_refused':True,'ICU_UTF8_lowercase':True,'invalid_converter_refused':True,'private_runtime_wildcard_and_exception':True,'recovery_cycles':2}
 for base,key in [('compile','artifacts'),('stage','stage_sha256')]:
  for name,sha in result[key].items():assert digest(work/base/name)==sha
 return result
