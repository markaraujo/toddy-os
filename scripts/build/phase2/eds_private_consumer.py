"""Correct staging-only private-library discovery; do not replay EDS originals."""
from pathlib import Path
import hashlib,json,os,subprocess,sys,xml.etree.ElementTree as ET
p=Path('/build');assert not (p/'stage-results.json').exists()
def digest(f):
    with f.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
consumer=p/'consumer-3.c';assert consumer.read_text()==sys.argv[1]
assert 'eds_major_version==3' in consumer.read_text() and not (p/'native-probe-4').exists()
before=json.loads((p/'ELFs-before-consumer-3.json').read_text());stage=json.loads((p/'stage-before-consumer-3.json').read_text())
for base,manifest in [('compile',before),('stage',stage)]:
    for name,sha in manifest.items():assert digest(p/base/name)==sha,name
assert (p/'stage/usr/lib/evolution-data-server/libedbus-private.so').is_file()
env={**os.environ,'PKG_CONFIG_PATH':'/stage/usr/lib/pkgconfig','LD_LIBRARY_PATH':'/stage/usr/lib:/stage/usr/lib/evolution-data-server'}
flags=subprocess.check_output(['pkg-config','--cflags','--libs','libecal-2.0'],env=env,text=True).split()
subprocess.run(['cc',str(consumer),'-I/stage/usr/include/evolution-data-server','-L/stage/usr/lib',*flags,'-Wl,-rpath,/stage/usr/lib','-Wl,-rpath-link,/stage/usr/lib','-Wl,-rpath-link,/stage/usr/lib/evolution-data-server','-o','/build/native-probe-4'],env=env,check=True)
r=subprocess.run(['/build/native-probe-4'],env=env,text=True,capture_output=True,timeout=30)
(p/'native-consumer-4.json').write_text(r.stdout);(p/'native-consumer-4.stderr').write_text(r.stderr);assert r.returncode==0
for base,manifest in [('compile',before),('stage',stage)]:
    for name,sha in manifest.items():assert digest(p/base/name)==sha,name
tests=[]
for c in ET.parse(p/'original-tests.xml').findall('.//testcase'):
    assert c.find('failure') is None and c.find('error') is None and c.find('skipped') is None
    tests.append({'name':c.get('name'),'result':'PASS'})
assert len(tests)==101
result={'scope':'All101original EDS/private DBus/calendar/contact/storage programs passed. Own version-variable and staged private-library discovery corrected consumer-only4; original ELFs/stage unchanged. Actual native UTF8/ICS/ESource/refusal/prior-state/recovery; installed services/schema union/GNOME/remote providers pending.', 'compile_exit':0,'stage_exit':0,'original_tests':tests,'consumer':json.loads(r.stdout),'prior_ELFs_unchanged_by_consumer_correction':True,'stage_unchanged_by_consumer_correction':True,'artifacts':before,'stage_sha256':stage}
(p/'stage-results.json').write_text(json.dumps(result,indent=2)+'\n')
