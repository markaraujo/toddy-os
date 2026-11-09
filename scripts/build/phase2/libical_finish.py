"""Reuse65original passes; run unchanged recur with byte-identical private file."""
from pathlib import Path
import hashlib,json,subprocess,sys,xml.etree.ElementTree as ET
p=Path('/build');assert not (p/'stage-results.json').exists() and not list(Path('/stage').iterdir())
def digest(f):
 with f.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
def elfs():return {str(f.relative_to(p/'compile')):digest(f) for f in (p/'compile').rglob('*') if f.is_file() and not f.is_symlink() and f.open('rb').read(4)==b'\x7fELF'}
before=elfs();assert before
cases=ET.parse(p/'original-tests.xml').findall('.//testcase');passed=[c.get('name') for c in cases if c.find('failure') is None and c.find('skipped') is None and c.find('error') is None]
assert len(cases)==66 and len(passed)==65 and {c.get('name') for c in cases}-set(passed)=={'recur'}
source=Path('/src/test-data/recur.txt');sha=digest(source);private=p/'recur-private-2.txt';assert not private.exists();private.write_bytes(source.read_bytes());private.chmod(0o600)
with (p/'recur-2.log').open('x') as log:r=subprocess.run(['/build/compile/src/test/recur',str(private)],stdout=log,stderr=subprocess.STDOUT,timeout=30)
(p/'recur-2.exit').write_text(str(r.returncode)+'\n');assert r.returncode==0
assert digest(source)==sha and digest(private)==sha
private.unlink();assert not private.exists() and elfs()==before
subprocess.run(['cmake','--install','/build/compile'],env={**__import__('os').environ,'DESTDIR':'/stage'},check=True)
subprocess.run(['cc','/src/toddy-probe.c','-I/stage/usr/include','-L/stage/usr/lib','-lical','-Wl,-rpath,/stage/usr/lib','-o','/build/native-probe'],check=True)
r=subprocess.run(['/build/native-probe'],capture_output=True,text=True,timeout=15);(p/'native-consumer.json').write_text(r.stdout);(p/'native-consumer.stderr').write_text(r.stderr);assert r.returncode==0
assert elfs()==before
result={'scope':'65original CTest passes reused plus unchanged recur executable with byte-identical private file; native UTF8/recurrence/refusal/recovery, not EDS/GNOME UI','compile_exit':0,'stage_exit':0,'reused_original_tests':passed,'repaired_original_test':{'name':'recur','exit':0,'source_fixture_sha256':sha,'fixture_contents_unchanged':True,'private_fixture_removed':True,'log_sha256':digest(p/'recur-2.log')},'consumer':json.loads(r.stdout),'unchanged_original_elfs':before,'stage_sha256':{str(f.relative_to(p/'stage')):digest(f) for f in (p/'stage').rglob('*') if f.is_file() and not f.is_symlink()}}
(p/'stage-results.json').write_text(json.dumps(result,indent=2)+'\n')
