"""Require original private-bus fixtures and native binary/schema/lifecycle APIs."""
import hashlib,json
from pathlib import Path
def digest(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def qualify(root):
 source=Path('/mnt/lfs/sources/phase2/inputs/libsecret-0.21.7');work=Path('/mnt/lfs/sources/phase2/work/libsecret-1');log=Path('/var/log/toddy/phase2')
 for a,b in [('toddy-build.sh','libsecret-build.sh'),('toddy-probe.c','libsecret-probe.c')]:assert (source/a).read_bytes()==(root/'scripts/build/phase2'/b).read_bytes()
 assert (log/'libsecret-1.exit').read_text().strip()=='0'
 assert json.loads((log/'libsecret-1.job.json').read_text())['command'][2:]==[str(source),str(work),'dbus-run-session','--','bash','/src/toddy-build.sh']
 result=json.loads((work/'stage-results.json').read_text());assert result['compile_exit']==result['stage_exit']==0
 rows=[json.loads(s) for s in (work/'compile/meson-logs/testlog.json').read_text().splitlines() if s.strip()]
 assert len(rows)==22 and all(r['result']=='OK' and r['returncode']==0 for r in rows)
 assert result['original_tests']==[{k:r[k] for k in ['name','result','returncode']} for r in rows] and result['original_nested_skips']==[]
 assert result['consumer']=={'binary_value_preserved':True,'nontext_value_refused_as_text':True,'typed_schema_attributes':True,'lifecycle_cycles':2,'real_credentials_used':False}
 assert result['gi']['native_gi_types']==['SecretValue','SecretService']
 for base,key in [('compile','artifacts'),('stage','stage_sha256')]:
  for name,sha in result[key].items():assert digest(work/base/name)==sha
 return result
