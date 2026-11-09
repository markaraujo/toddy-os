"""Correct only own PEM consumer; reuse all six original passes and stage."""
from pathlib import Path
import hashlib,json,os,subprocess,sys
p=Path('/build');assert not (p/'stage-results.json').exists()
def digest(f):
    with f.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
assert digest(Path('/src/toddy-probe.c'))=='6c7b917684f956fa15ef94f01aebc551e7cf6c981c7a660ab299b1e4a8626acd'
assert 'root && !error' in (p/'native-consumer.stderr').read_text()
assert (p/'TLS-remaining-2.exit').read_text().strip()=='0'
initial=[json.loads(s) for s in (p/'initial-testlog-1.json').read_text().splitlines() if s.strip()]
remaining=[json.loads(s) for s in (p/'remaining-testlog-2.json').read_text().splitlines() if s.strip()]
tests=[t for t in initial if t['result']=='OK']+remaining
assert len(tests)==6 and len({t['name'] for t in tests})==6 and all(t['result']=='OK' and t['returncode']==0 for t in tests)
before=json.loads((p/'ELFs-before-TLS-2.json').read_text())
assert all(digest(p/'compile'/name)==sha for name,sha in before.items())
stage={str(f.relative_to(p/'stage')):digest(f) for f in (p/'stage').rglob('*') if f.is_file() and not f.is_symlink()}
assert stage and not (p/'stage-before-consumer-3.json').exists()
(p/'stage-before-consumer-3.json').write_text(json.dumps(stage,indent=2)+'\n')
consumer=p/'consumer-3.c';assert not consumer.exists();consumer.write_text(sys.argv[1])
flags=subprocess.check_output(['pkg-config','--cflags','--libs','gio-2.0'],text=True).split()
subprocess.run(['cc',str(consumer),*flags,'-o','/build/native-probe-3'],check=True)
env={**os.environ,'GIO_MODULE_DIR':'/stage/usr/lib/gio/modules','GIO_USE_TLS':'gnutls'}
r=subprocess.run(['/build/native-probe-3'],env=env,text=True,capture_output=True,timeout=30)
(p/'native-consumer-3.json').write_text(r.stdout);(p/'native-consumer-3.stderr').write_text(r.stderr);assert r.returncode==0
assert all(digest(p/'compile'/name)==sha for name,sha in before.items())
assert all(digest(p/'stage'/name)==sha for name,sha in stage.items())
result={'scope':'All six enabled original proxy/certificate/database/TLS drivers qualified with actual read-only factory trust. Three initial missing-root failures retained. Only own C input corrected from OpenSSL auxiliary PEM to standard PEM bundle; original tests/stage not repeated. Native GIO/default root/malformed certificate refusal/recovery; DTLS/remote network/installed shared cache/native GNOME pending.', 'compile_exit':0,'stage_exit':0,'original_tests':[{k:t[k] for k in ['name','result','returncode']} for t in tests], 'initial_failed_tests_retained':True,'public_trust_readonly':True,'prior_ELFs_unchanged':True,'stage_unchanged_by_consumer_correction':True,'consumer':json.loads(r.stdout),'artifacts':before,'stage_sha256':stage}
(p/'stage-results.json').write_text(json.dumps(result,indent=2)+'\n')
