"""Bind frozen VTE originals and the two distinct retained consumer recoveries."""
from pathlib import Path
import hashlib,json

def digest(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def qualify(root):
 s=Path('/mnt/lfs/sources/phase2/inputs/vte-0.84.1');w=Path('/mnt/lfs/sources/phase2/work/vte-1');l=Path('/var/log/toddy/phase2')
 assert (s/'toddy-build.sh').read_bytes()==(root/'scripts/build/phase2/vte-build.sh').read_bytes()
 assert json.loads((s/'toddy-prepared.json').read_text())['source_sha256']=='9f73468982a339cd1eb942beb7d348a5564c9ed48473ad1690c791f8474916ec'
 assert (w/'original-tests.exit').read_text().strip()=='0'
 r=json.loads((w/'stage-results.json').read_text());assert r['compile_exit']==r['stage_exit']==0
 rows=[json.loads(x) for x in (w/'compile/meson-logs/testlog.json').read_text().splitlines() if x.strip()]
 assert len(rows)==18 and all(x['result']=='OK' and x['returncode']==0 for x in rows)
 assert r['original_tests']==[{k:x[k] for k in ['name','result','returncode']} for x in rows]
 assert len(json.loads((w/'original-registered-tests.json').read_text()))==18
 assert len(r['artifacts'])==134 and len(r['stage_sha256'])==125
 for base,key in [('compile','artifacts'),('stage','stage_sha256')]:
  for name,sha in r[key].items():assert digest(w/base/name)==sha
 if (l/'vte-probe-3.exit').exists():
  assert (l/'vte-1.exit').read_text().strip()=='1' and 'PTY creation' in (l/'vte-1.log').read_text()
  assert (l/'vte-probe-2.exit').read_text().strip()=='1' and 'actual child marker absent' in (l/'vte-probe-2.log').read_text()
  assert (l/'vte-probe-3.exit').read_text().strip()=='0'
  assert digest(s/'toddy-probe.c')=='0a3113eaca83adc1fb6d566515d56217adbac9ba94f6604681b647373baf2ee1'
  assert (w/'probe-3/probe.c').read_bytes()==(root/'scripts/build/phase2/vte-probe.c').read_bytes()
  code=(root/'scripts/build/phase2/vte_packet_probe_resume.py').read_text()+'\nmain('+repr((root/'scripts/build/phase2/vte-probe.c').read_text())+')\n'
  assert json.loads((l/'vte-probe-3.job.json').read_text())['command'][-3:]==['python3','-c',code]
  before=json.loads((w/'probe-2/before.json').read_text())
  assert all(before[k]==r[k] for k in ['artifacts','stage_sha256'])
  assert r['probe_only_recovery']['compile_and_stage_unchanged'] and r['probe_only_recovery']['TIOCPKT_control_bytes_decoded']
 else:
  assert (l/'vte-1.exit').read_text().strip()=='0'
  assert (s/'toddy-probe.c').read_bytes()==(root/'scripts/build/phase2/vte-probe.c').read_bytes()
 assert r['consumer']=={'version':'0.84.1','regex_compile_replace':True,'invalid_regex_refused':True,'PTY_resize_UTF8':True,'normal_shell_cycles':3,'managed_process_group_Stop':True,'fresh_PTY_after_Stop':True,'interactive_owner_prompt_hook_preserved':True,'GTK_GNOME_Terminal_or_display_tested':False}
 assert r['GI_consumer']=={'namespace':'Vte2.91','runtime_version':'0.84.1','widget_or_display_tested':False}
 assert digest(w/'stage/etc/profile.d/vte.sh')==r['shell_integration']['after_sha256']
 assert digest(w/'stage/usr/share/doc/vte/preserve-user-prompt-command.patch')==r['shell_integration']['patch_sha256']
 return r
