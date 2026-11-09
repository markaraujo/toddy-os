"""Run only not-yet-run certificate/slow/fuzz originals; preserve earlier results."""
from pathlib import Path
import hashlib,json,re,subprocess
p=Path('/build');assert not (p/'certificate-results-3.json').exists() and not list(Path('/stage').iterdir())
def digest(f):
 with f.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
before={str(f.relative_to(p/'compile')):digest(f) for f in (p/'compile').rglob('*') if f.is_file() and not f.is_symlink() and f.open('rb').read(4)==b'\x7fELF'}
records={}
for f in (p/'compile').rglob('*.trs'):
 m=re.search(r'^:test-result: (\S+)$',f.read_text(),re.M);assert m;records[str(f.relative_to(p/'compile'))]={'result':m[1],'sha256':digest(f),'log_sha256':digest(f.with_suffix('.log'))}
assert len(records)==813 and sum(r['result']=='PASS' for r in records.values())==725 and sum(r['result']=='SKIP' for r in records.values())==86
assert {name for name,r in records.items() if r['result']=='FAIL'}=={'src/gl/tests/test-getaddrinfo.trs','tests/trust-store.trs'}
(p/'original-records-before-certificates-3.json').write_text(json.dumps(records,indent=2)+'\n');(p/'ELFs-before-certificates-3.json').write_text(json.dumps(before,indent=2)+'\n')
runs=[]
for directory in ['tests/cert-tests','tests/slow','fuzz']:
 assert not list((p/'compile'/directory).rglob('*.trs')),'Reconcile existing test postconditions before any replay'
 label=directory.replace('/','-')
 with (p/('certificates-3-'+label+'.log')).open('x') as log:r=subprocess.run(['make','-C','/build/compile/'+directory,'-j4','check'],stdout=log,stderr=subprocess.STDOUT)
 runs.append({'directory':directory,'exit':r.returncode});(p/'certificate-progress-3.json').write_text(json.dumps(runs,indent=2)+'\n')
 if r.returncode:raise SystemExit(r.returncode)
for name,row in records.items():assert digest(p/'compile'/name)==row['sha256'] and digest((p/'compile'/name).with_suffix('.log'))==row['log_sha256']
assert all(digest(p/'compile'/name)==sha for name,sha in before.items())
(p/'certificate-results-3.json').write_text(json.dumps({'scope':'Only remaining original certificate/slow/fuzz drivers. Earlier725passes/86skips and two original failures retained; default trust repaired separately with genuine staged CA data, public DNS remains unqualified','runs':runs,'prior_records_unchanged':records,'prior_ELFs_unchanged':before},indent=2)+'\n')
