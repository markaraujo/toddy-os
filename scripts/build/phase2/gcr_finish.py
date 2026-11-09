"""Stage once after composed original outcomes, then new native transport/GI checks."""
from pathlib import Path
import hashlib,json,os,re,subprocess,sys
p=Path('/build');assert not list(Path('/stage').iterdir()) and not (p/'stage-results.json').exists()
def artifacts():return {str(f.relative_to(p/'compile')):hashlib.sha256(f.read_bytes()).hexdigest() for f in (p/'compile').rglob('*') if f.is_file() and not f.is_symlink() and f.open('rb').read(4)==b'\x7fELF'}
before=artifacts();initial=[json.loads(s) for s in (p/'initial-testlog-1.json').read_text().splitlines() if s.strip()]
passed=[r for r in initial if r['result']=='OK' and r['returncode']==0];assert len(initial)==39 and len(passed)==38
partial=json.loads((p/'askpass-2.json').read_text());assert partial['exit']==0 and partial['unchanged_original_elfs']==before
partial_rows=[json.loads(s) for s in (p/'compile/meson-logs/testlog.json').read_text().splitlines() if s.strip()];assert len(partial_rows)==1
text=partial_rows[0]['stdout'];assert re.search(r'^ok \d+ /gcr/ssh-askpass/properties$',text,re.M)
assert len(re.findall(r'^ok \d+.*# SKIP ssh-keygen not found$',text,re.M))==2
repaired=json.loads((p/'askpass-cases-3.json').read_text());assert repaired['unchanged_original_elfs']==before and {r['name'] for r in repaired['runs']}=={'ssh-keygen','cancelled'} and all(r['exit']==0 and r['expected_outcome_passed'] for r in repaired['runs'])
for r in repaired['runs']:
 for stream in ['stdout','stderr']:
  raw=(p/('askpass-3-'+r['name']+'.'+stream)).read_bytes();assert hashlib.sha256(raw).hexdigest()==r[stream+'_sha256']
assert repaired['private_sample_sha256']=='55b32dbd31618e5e949be919fb42ed7ca519f8e4ad5b352c9136ab7202e6ef4e'
r=subprocess.run(['meson','install','-C','/build/compile','--destdir','/stage','--no-rebuild']);(p/'gcr-stage-4.exit').write_text(str(r.returncode)+'\n');assert r.returncode==0
probe=p/'native-transport-4.c';probe.write_text(sys.argv[1])
flags=subprocess.check_output(['pkg-config','--cflags','--libs','gio-2.0','gobject-2.0','p11-kit-1'],text=True).split()
subprocess.run(['cc',str(probe),'-I/stage/usr/include/gcr-4','-I/stage/usr/include/gck-2','-L/stage/usr/lib','-lgcr-4','-lgck-2',*flags,'-Wl,-rpath,/stage/usr/lib','-o','/build/native-probe'],check=True)
env=dict(os.environ,LD_LIBRARY_PATH='/stage/usr/lib',GI_TYPELIB_PATH='/stage/usr/lib/girepository-1.0')
r=subprocess.run(['/build/native-probe'],env=env,capture_output=True,text=True,timeout=20);(p/'native-consumer.json').write_text(r.stdout);(p/'native-consumer.stderr').write_text(r.stderr);(p/'native-consumer-4.exit').write_text(str(r.returncode)+'\n');assert r.returncode==0
gi="import gi,json\ngi.require_version('Gcr','4');gi.require_version('Gck','2')\nfrom gi.repository import Gcr,Gck\nassert Gcr.SecretExchange.__gtype__.name=='GcrSecretExchange' and Gck.Module.__gtype__.name=='GckModule'\nprint(json.dumps({'native_gi_types':['GcrSecretExchange','GckModule'],'scope':'GI types only; graphical prompt pending'}))"
r=subprocess.run(['python3','-c',gi],env=env,capture_output=True,text=True,timeout=20,check=True);(p/'native-gi.json').write_text(r.stdout)
assert artifacts()==before
result={'scope':'38reused original Gcr/Gck/egg programs plus three repaired original askpass cases; native transport/GI only, no graphical credential prompt/keyring/real credential acceptance','compile_exit':0,'stage_exit':0,'reused_original_programs':38,'original_tests':[{k:r[k] for k in ['name','result','returncode']} for r in passed],'original_nested_skips':[{'program':r['name'],'line':s} for r in passed for s in r.get('stdout','').splitlines() if re.match(r'^ok \d+.*#\s*SKIP',s,re.I)],'repaired_original_askpass_cases':[{'name':'properties','exit':0},*repaired['runs']],'consumer':json.loads((p/'native-consumer.json').read_text()),'gi':json.loads((p/'native-gi.json').read_text()),'unchanged_original_elfs':before,'stage_sha256':{str(f.relative_to(p/'stage')):hashlib.sha256(f.read_bytes()).hexdigest() for f in (p/'stage').rglob('*') if f.is_file() and not f.is_symlink()}}
(p/'stage-results.json').write_text(json.dumps(result,indent=2)+'\n')
