"""Qualify only own corrected EDS C consumer after successful original tests/stage."""
from pathlib import Path
import hashlib,json,os,subprocess,sys,xml.etree.ElementTree as ET
p=Path('/build');assert not (p/'stage-results.json').exists()
def digest(f):
    with f.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
old=Path('/src/toddy-probe.c').read_text()
assert hashlib.sha256(old.encode()).hexdigest()=='e435a41a331a145878c3f878bbdc0ec30d9dc996c6e178c49638535cea816954'
expected=old.replace('eds_major_version()','eds_major_version').replace('eds_minor_version()','eds_minor_version').replace('eds_micro_version()','eds_micro_version')
assert sys.argv[1]==expected
tests=[]
for c in ET.parse(p/'original-tests.xml').findall('.//testcase'):
    assert c.find('failure') is None and c.find('error') is None
    tests.append({'name':c.get('name'),'result':'SKIP' if c.find('skipped') is not None else 'PASS'})
assert len(tests)==101 and all(t['result']=='PASS' for t in tests)
assert (p/'compile/install_manifest.txt').is_file()
before={str(f.relative_to(p/'compile')):digest(f) for f in (p/'compile').rglob('*') if f.is_file() and not f.is_symlink() and f.open('rb').read(4)==b'\x7fELF'}
stage={str(f.relative_to(p/'stage')):digest(f) for f in (p/'stage').rglob('*') if f.is_file() and not f.is_symlink()}
assert stage
consumer=p/'consumer-3.c';assert not consumer.exists();consumer.write_text(expected)
(p/'ELFs-before-consumer-3.json').write_text(json.dumps(before,indent=2)+'\n')
(p/'stage-before-consumer-3.json').write_text(json.dumps(stage,indent=2)+'\n')
env={**os.environ,'PKG_CONFIG_PATH':'/stage/usr/lib/pkgconfig','LD_LIBRARY_PATH':'/stage/usr/lib'}
flags=subprocess.check_output(['pkg-config','--cflags','--libs','libecal-2.0'],env=env,text=True).split()
subprocess.run(['cc',str(consumer),'-I/stage/usr/include/evolution-data-server','-L/stage/usr/lib',*flags,'-Wl,-rpath,/stage/usr/lib','-Wl,-rpath-link,/stage/usr/lib','-o','/build/native-probe-3'],env=env,check=True)
r=subprocess.run(['/build/native-probe-3'],env=env,text=True,capture_output=True,timeout=30)
(p/'native-consumer-3.json').write_text(r.stdout);(p/'native-consumer-3.stderr').write_text(r.stderr);assert r.returncode==0
assert all(digest(p/'compile'/name)==sha for name,sha in before.items())
assert all(digest(p/'stage'/name)==sha for name,sha in stage.items())
result={'scope':'All101original EDS/private DBus/calendar/contact/storage programs passed, no skips. Only own version-variable checker corrected consumer-only3; original ELFs/stage unchanged. Actual native UTF8/ICS/ESource/refusal/prior-state/recovery; installed services/schema union/native GNOME/remote providers pending.', 'compile_exit':0,'stage_exit':0,'original_tests':tests,'consumer':json.loads(r.stdout),'prior_ELFs_unchanged_by_consumer_correction':True,'stage_unchanged_by_consumer_correction':True,'artifacts':before,'stage_sha256':stage}
(p/'stage-results.json').write_text(json.dumps(result,indent=2)+'\n')
