"""Finish only the new staged consumer after the missing system-bus CLI diagnosis."""
from pathlib import Path
import hashlib,json,re,subprocess,sys,os
p=Path('/build');assert not (p/'stage-results.json').exists()
def artifacts():return {str(f.relative_to(p/'compile')):hashlib.sha256(f.read_bytes()).hexdigest() for f in (p/'compile').rglob('*') if f.is_file() and not f.is_symlink() and f.open('rb').read(4)==b'\x7fELF'}
before=artifacts();assert before
text=(p/'original-portable.log').read_text();passes=re.findall(r'^ok \d+ (/[a-z_/]+)$',text,re.M)
assert set(passes)=={'/power/backend','/power/device','/power/device_list','/power/history','/power/native'} and len(passes)==5
assert 'not ok' not in text and 'No system D-BUS running' not in text
skips=re.findall(r'^ok \d+ (/[a-z_/]+) # SKIP by request.*$',text,re.M);assert set(skips)=={'/power/polkit','/power/daemon'}
env=dict(os.environ,LD_LIBRARY_PATH='/stage/usr/lib',GI_TYPELIB_PATH='/stage/usr/lib/girepository-1.0')
r=subprocess.run(['python3','-c',sys.argv[1],'/stage'],env=env,capture_output=True,text=True,timeout=15);(p/'consumer-4.stdout').write_text(r.stdout);(p/'consumer-4.stderr').write_text(r.stderr);r.check_returncode();consumer=json.loads(r.stdout)
assert artifacts()==before
result={'scope':'Five reused original portable tests and repaired CLI-help/GI/history consumer only; no real power/device/service acceptance','compile_exit':0,'stage_exit':0,'original_portable_cases':passes,'excluded_system_bus_cases':skips,'umockdev_matrix':'Not qualified; requires optional Umockdev dependency and device fixtures','consumer':consumer,'unchanged_original_elfs':before,'stage_sha256':{str(f.relative_to(p/'stage')):hashlib.sha256(f.read_bytes()).hexdigest() for f in (p/'stage').rglob('*') if f.is_file() and not f.is_symlink()}}
(p/'stage-results.json').write_text(json.dumps(result,indent=2)+'\n')
