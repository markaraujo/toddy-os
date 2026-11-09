"""Verify successful CLI result and finish stage/consumer without replay."""
from pathlib import Path
import hashlib,json,os,re,subprocess
assert os.getuid()==101
p=Path('/build');assert not (p/'stage-results.json').exists() and not list((p/'stage').iterdir())
old=(p/'original-tests.log').read_text();assert '96% tests passed, 1 tests failed out of 28' in old
passed=set(re.findall(r'Test\s+#\d+:\s+(\S+)\s+[^\n]*Passed',old));assert len(passed)==27
assert '100% tests passed out of 1' in (p/'cli-only-tests.log').read_text()
last=(p/'compile/Testing/Temporary/LastTest.log').read_text();assert last.count('Test Passed.')==1 and 'Test Failed.' not in last and 'test_json_parse_cli' in last
before=json.loads((p/'original-elfs-1.json').read_text())
for name,sha in before.items():
 with (p/'compile'/name).open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==sha
with (p/'stage.log').open('x') as log:subprocess.run(['cmake','--install','/build/compile'],env={**os.environ,'DESTDIR':'/stage'},stdout=log,stderr=subprocess.STDOUT,check=True)
assert not (p/'stage/usr/bin/json_parse').exists()
subprocess.run(['cc','-Wall','-Wextra','-Werror','/src/toddy-probe.c','-I/stage/usr/include','-L/stage/usr/lib','-Wl,-rpath,/stage/usr/lib','-ljson-c','-o','/build/consumer'],check=True)
with (p/'native-consumer.json').open('x') as log:subprocess.run(['/build/consumer'],stdout=log,check=True)
registered=json.loads(subprocess.check_output(['ctest','--test-dir','/build/compile','--show-only=json-v1'],text=True))['tests']
assert {r['name'] for r in registered}==passed|{'test_json_parse_cli'} and len(registered)==28
result={'scope':'Original JSON-C28programs composed from27unchanged passes and only repaired build-only CLI fixture; actual strict typed/UTF8/depth/refusal/recovery C consumer, no AccountsService/GNOME acceptance','compile_exit':0,'stage_exit':0,'original_programs':28,'reused_original_programs':27,'corrected_original_programs':1,'original_failure_retained':'BUILD_APPS=OFF left original security CLI fixture executable absent; upstream builds but never installs this application','unchanged_original_elfs':before,'consumer':json.loads((p/'native-consumer.json').read_text()),'profile':'Partial atomic reference counting enabled, not general object thread safety; hardware RDRAND/extra libraries/static library disabled; upstream test CLI not installed','stage_sha256':{str(f.relative_to(p/'stage')):hashlib.sha256(f.read_bytes()).hexdigest() for f in (p/'stage').rglob('*') if f.is_file() and not f.is_symlink()}}
(p/'stage-results.json').write_text(json.dumps(result,indent=2)+'\n')
