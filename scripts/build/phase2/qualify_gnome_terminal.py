"""Bind Terminal compile/regex and exact cache-only book correction/recovery."""
from pathlib import Path
import hashlib,json

def digest(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def qualify(root):
 s=Path('/mnt/lfs/sources/phase2/inputs/gnome-terminal-3.60.0');w=Path('/mnt/lfs/sources/phase2/work/gnome-terminal-1');l=Path('/var/log/toddy/phase2')
 prep=json.loads((s/'toddy-prepared.json').read_text());assert prep['source_sha256']=='6c006523d2c21282fd62c64fc44f63546aaa216e66eb439b8129af68db11df7c'
 r=json.loads((w/'stage-results.json').read_text());assert r['compile_exit']==r['stage_exit']==0
 assert (w/'original-tests.exit').read_text().strip()=='0';rows=[json.loads(x) for x in (w/'compile/meson-logs/testlog.json').read_text().splitlines() if x.strip()]
 assert len(rows)==1 and rows[0]['name']=='gnome-terminal:regex' and rows[0]['result']=='OK' and rows[0]['returncode']==0
 assert r['original_tests']==[{k:x[k] for k in ['name','result','returncode']} for x in rows]
 assert len(r['artifacts'])==71 and len(r['stage_sha256'])==116
 for base,key in [('compile','artifacts'),('stage','stage_sha256')]:
  for name,sha in r[key].items():assert digest(w/base/name)==sha
 if (l/'gnome-terminal-probe-3.exit').exists():
  assert (l/'gnome-terminal-1.exit').read_text().strip()=='1' and "Program 'xsltproc' not found" in (l/'gnome-terminal-1.log').read_text()
  assert digest(s/'toddy-build.sh')==prep['recipe_sha256']=='7d2ee1b3beaca6e242ac9f5d6c2a951cbc9246cc8bc2fb473cc6c3a316f91d6a'
  assert digest(s/'toddy-probe.py')=='9444390b087e7031089a1e600f039f3a833d3fd5e157531bfb7fe34f8b66b986'
  assert (l/'gnome-terminal-build-2.exit').read_text().strip()=='1' and "profiles.get_strv('list')==[]" in (l/'gnome-terminal-build-2.log').read_text()
  old=(s/'toddy-build.sh').read_text();code=(root/'scripts/build/phase2/gnome_terminal_resume.py').read_text()+'\nmain('+repr(old)+')\n'
  assert json.loads((l/'gnome-terminal-build-2.job.json').read_text())['command'][-3:]==['python3','-c',code]
  assert (l/'gnome-terminal-probe-3.exit').read_text().strip()=='0'
  probe=(root/'scripts/build/phase2/gnome-terminal-probe.py').read_text();correction=(root/'scripts/build/phase2/gnome_terminal_schema.py').read_text()
  code=(root/'scripts/build/phase2/gnome_terminal_probe_resume.py').read_text()+'\nmain('+repr(probe)+','+repr(correction)+')\n'
  assert json.loads((l/'gnome-terminal-probe-3.job.json').read_text())['command'][-3:]==['python3','-c',code]
  assert (w/'probe-3/probe.py').read_text()==probe and (w/'probe-3/schema.py').read_text()==correction
  before=json.loads((w/'probe-3/before.json').read_text());assert before['artifacts']==r['artifacts']
  changed={key for key in set(before['stage_sha256'])|set(r['stage_sha256']) if before['stage_sha256'].get(key)!=r['stage_sha256'].get(key)}
  assert changed=={'usr/lib/gnome-terminal/gschemas.compiled','usr/share/doc/gnome-terminal/external-schema-paths.patch'}
  correction=r['schema_correction'];assert correction['compiled_ELFs_unchanged'] and correction['preserved_schemas']==12 and correction['preserved_key_type_default_range_contracts']==146 and len(correction['changed_schema_paths'])==5
  assert digest(s/'src/external.gschema.xml')==correction['source_before_sha256']
  assert digest(w/'stage/usr/lib/gnome-terminal/gschemas.compiled')==correction['stage_cache_after_sha256']
  assert digest(w/'stage/usr/share/doc/gnome-terminal/external-schema-paths.patch')==correction['patch_sha256']
  assert r['actual_unknown_option_error_verified']
 else:
  assert (l/'gnome-terminal-1.exit').read_text().strip()=='0'
  assert (s/'toddy-build.sh').read_bytes()==(root/'scripts/build/phase2/gnome-terminal-build.sh').read_bytes()
  assert (s/'toddy-probe.py').read_bytes()==(root/'scripts/build/phase2/gnome-terminal-probe.py').read_bytes()
  patch=prep['source_patches'];assert len(patch)==1 and patch[0]['changed_paths']==5 and patch[0]['after_sha256']==digest(s/'src/external.gschema.xml')
 c=r['consumer'];assert c['client_version']=='3.60.0' and c['invalid_CLI_option_refused'] and c['private_DConf_file'] and not c['widget_or_display_tested']
 assert c['profile_cycles']==[{'typed_profile_written':True,'invalid_boolean_refused_state_preserved':True,'system_font_preserved':True},{'persisted_after_bus_restart':True,'reset_recovered_defaults':True,'system_font_preserved':True}]
 return r
