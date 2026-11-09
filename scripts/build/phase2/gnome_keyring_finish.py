"""Stage only unchanged production Keyring after separate original fixture checks."""
from pathlib import Path
import hashlib,json,subprocess,sys
p=Path('/build');assert not list(Path('/stage').iterdir()) and not (p/'stage-results.json').exists()
def digest(path):
 with path.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def artifacts():return {str(f.relative_to(p/'compile')):digest(f) for f in (p/'compile').rglob('*') if f.is_file() and not f.is_symlink() and f.open('rb').read(4)==b'\x7fELF'}
fixture=json.loads((p/'fixture-results-2.json').read_text());assert fixture['production_original_programs']==57 and len(fixture['fixture_programs'])==5
assert fixture['production_debug_mode'] is False and fixture['fixture_debug_mode'] is True and fixture['fixture_never_staged']
for r in fixture['fixture_programs']:
 assert r['exit']==r['returncode']==0 and r['result']=='OK'
 for suffix,key in [('log','log_sha256'),('json','record_sha256')]:assert digest(p/('fixture-2-'+r['name']+'.'+suffix))==r[key]
before=artifacts();assert before==fixture['production_elfs_unchanged']
rows=[json.loads(s) for s in (p/'production-testlog-before-fixtures-2.json').read_text().splitlines() if s.strip()];passed=[r for r in rows if r['result']=='OK' and r['returncode']==0];assert len(passed)==57
options={r['name']:r['value'] for r in json.loads((p/'compile/meson-info/intro-buildoptions.json').read_text())};assert options['debug-mode'] is False
r=subprocess.run(['meson','install','-C','/build/compile','--destdir','/stage','--no-rebuild']);(p/'production-stage-3.exit').write_text(str(r.returncode)+'\n');assert r.returncode==0
r=subprocess.run(['python3','-c',sys.argv[1],'/stage'],capture_output=True,text=True,timeout=20);(p/'native-consumer.json').write_text(r.stdout);(p/'native-consumer.stderr').write_text(r.stderr);(p/'native-consumer-3.exit').write_text(str(r.returncode)+'\n');assert r.returncode==0
assert artifacts()==before
result={'scope':'57original production programs plus5original PRIVATE fixture-only programs, not production fixture passes. Production CLI/PAM ABI only; actual production secret backend/native PAM/GUI gate pending','compile_exit':0,'stage_exit':0,'production_original_programs':57,'production_original_tests':[{k:r[k] for k in ['name','result','returncode']} for r in passed],'fixture_original_programs':fixture['fixture_programs'],'private_fixture_daemon_sha256':fixture['fixture_daemon_sha256'],'production_debug_mode':False,'fixture_debug_only':True,'consumer':json.loads((p/'native-consumer.json').read_text()),'unchanged_production_elfs':before,'stage_sha256':{str(f.relative_to(p/'stage')):digest(f) for f in (p/'stage').rglob('*') if f.is_file() and not f.is_symlink()}}
assert not any('fixture-debug' in name for name in result['stage_sha256'])
(p/'stage-results.json').write_text(json.dumps(result,indent=2)+'\n')
