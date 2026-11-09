"""Qualify native CLI/private schema stage; real graphical session remains separate."""
import hashlib,json
from pathlib import Path
def digest(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def qualify(root):
 source=Path('/mnt/lfs/sources/phase2/inputs/gnome-session-50.1');work=Path('/mnt/lfs/sources/phase2/work/gnome-session-1');log=Path('/var/log/toddy/phase2')
 for a,b in [('toddy-build.sh','gnome-session-build.sh'),('toddy-probe.py','gnome-session-probe.py')]:assert (source/a).read_bytes()==(root/'scripts/build/phase2'/b).read_bytes()
 assert (log/'gnome-session-1.exit').read_text().strip()=='0'
 assert json.loads((log/'gnome-session-1.job.json').read_text())['command'][2:]==[str(source),str(work),'bash','/src/toddy-build.sh']
 result=json.loads((work/'stage-results.json').read_text());assert result['compile_exit']==result['stage_exit']==0 and result['registered_original_tests']==0
 assert json.loads((work/'compile/meson-info/intro-tests.json').read_text())==[]
 consumer=result['consumer'];assert consumer['version']=='50.1' and len(consumer['help_runs'])==5 and all(r['help_exit']==0 for r in consumer['help_runs'])
 assert consumer['invalid_option_refused'] and consumer['wayland_session_and_systemd_target'] and consumer['private_schema_default_true_keys']==['logout-prompt','show-fallback-warning']
 for base,key in [('compile','artifacts'),('stage','stage_sha256')]:
  for name,sha in result[key].items():assert digest(work/base/name)==sha
 return result
