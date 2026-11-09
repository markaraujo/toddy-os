"""Bind production artifacts and private fixtures to their distinct actual jobs."""
import hashlib,json
from pathlib import Path
def digest(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def qualify(root):
 source=Path('/mnt/lfs/sources/phase2/inputs/gnome-keyring-50.0');work=Path('/mnt/lfs/sources/phase2/work/gnome-keyring-1');log=Path('/var/log/toddy/phase2')
 assert digest(source/'toddy-build.sh')=='f82dc0535bbbf6861a98f5e9f2596c8daccf23aad56a9be8b7c358fe29fbed70'
 assert digest(source/'toddy-probe.py')=='434613227c11f58e6046c7e3e3a06827faf468b07d8a893de6d46d477827c195'
 assert (log/'gnome-keyring-1.exit').read_text().strip()=='1'
 assert json.loads((log/'gnome-keyring-1.job.json').read_text())['command'][2:]==[str(source),str(work),'dbus-run-session','--','bash','/src/toddy-build.sh']
 for job,script,extra in [('gnome-keyring-fixtures-2','gnome_keyring_fixtures.py',[]),('gnome-keyring-stage-3','gnome_keyring_finish.py',[(root/'scripts/build/phase2/gnome-keyring-probe.py').read_text()]),('gnome-keyring-backend-4','gnome_keyring_backend.py',['/stage','/build/production-backend-4.json'])]:
  assert (log/(job+'.exit')).read_text().strip()=='0'
  cmd=[str(source),str(work),*(['dbus-run-session','--'] if job=='gnome-keyring-backend-4' else []),'python3','-c',(root/'scripts/build/phase2'/script).read_text(),*extra]
  assert json.loads((log/(job+'.job.json')).read_text())['command'][2:]==cmd
 result=json.loads((work/'stage-results.json').read_text());assert result['compile_exit']==result['stage_exit']==0 and result['production_original_programs']==57
 assert result['production_debug_mode'] is False and result['fixture_debug_only'] is True
 initial=[json.loads(s) for s in (work/'production-testlog-before-fixtures-2.json').read_text().splitlines() if s.strip()]
 passed=[r for r in initial if r['result']=='OK' and r['returncode']==0];assert len(initial)==62 and len(passed)==57
 assert result['production_original_tests']==[{k:r[k] for k in ['name','result','returncode']} for r in passed]
 assert {r['name'] for r in initial if r['result']!='OK'}=={'gkr-daemon-dbus - gnome-keyring:dbus-search','gkr-daemon-dbus - gnome-keyring:dbus-items','gkr-daemon-dbus - gnome-keyring:dbus-signals','gkr-daemon-dbus - gnome-keyring:dbus-lock','gkr-daemon-dbus - gnome-keyring:dbus-portal'}
 fixture=json.loads((work/'fixture-results-2.json').read_text());assert result['fixture_original_programs']==fixture['fixture_programs'] and len(fixture['fixture_programs'])==5 and fixture['fixture_never_staged']
 assert result['unchanged_production_elfs']==fixture['production_elfs_unchanged'] and len(result['unchanged_production_elfs'])==332
 for row in fixture['fixture_programs']:
  assert row['exit']==row['returncode']==0 and row['result']=='OK'
  for suffix,key in [('log','log_sha256'),('json','record_sha256')]:assert digest(work/('fixture-2-'+row['name']+'.'+suffix))==row[key]
 for base,key in [('compile','unchanged_production_elfs'),('stage','stage_sha256')]:
  for name,sha in result[key].items():assert digest(work/base/name)==sha
 assert result['consumer']['production_test_hooks_disabled'] is True
 backend=json.loads((work/'production-backend-4.json').read_text());assert backend['uid']==101 and backend['production_test_hooks_disabled'] and backend['no_mock_environment_supplied'] and backend['private_test_data_removed'] and backend['credential_values_or_ciphertext_retained'] is False
 assert backend['daemon_sha256']==digest(work/'stage/usr/bin/gnome-keyring-daemon')
 assert len(backend['runs'])==6 and all(r['passed'] for r in backend['runs']) and len(set(backend['distinct_bus_owners']))==3 and all(r['exit']==0 for r in backend['daemon_output_digests_only'])
 return result,backend
