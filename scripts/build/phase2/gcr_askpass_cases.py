from pathlib import Path
import hashlib,json,os,re,subprocess
p=Path('/build');assert not (p/'askpass-cases-3.json').exists()
def artifacts():return {str(f.relative_to(p/'compile')):hashlib.sha256(f.read_bytes()).hexdigest() for f in (p/'compile').rglob('*') if f.is_file() and not f.is_symlink() and f.open('rb').read(4)==b'\x7fELF'}
before=artifacts();env=dict(os.environ,PATH='/build/test-sdk/bin:/usr/bin:/usr/sbin',LD_LIBRARY_PATH='/build/compile/gcr:/build/compile/gck');runs=[]
assert (p/'test-sdk/bin/ssh-keygen').is_file()
for name in ['ssh-keygen','cancelled']:
 r=subprocess.run(['/build/compile/gcr/test-ssh-askpass','--tap','-p','/gcr/ssh-askpass/'+name],env=env,capture_output=True,text=True,timeout=30)
 (p/('askpass-3-'+name+'.stdout')).write_text(r.stdout);(p/('askpass-3-'+name+'.stderr')).write_text(r.stderr)
 passed=r.returncode==0 and not re.search('SKIP|not ok',r.stdout,re.I) and len(re.findall(r'^ok \d+ /gcr/ssh-askpass/'+name+'$',r.stdout,re.M))==1
 runs.append({'name':name,'exit':r.returncode,'expected_outcome_passed':passed,'stdout_sha256':hashlib.sha256(r.stdout.encode()).hexdigest(),'stderr_sha256':hashlib.sha256(r.stderr.encode()).hexdigest()})
assert artifacts()==before
result={'runs':runs,'unchanged_original_elfs':before,'private_sample_sha256':hashlib.sha256(Path('/src/gcr/fixtures/pem-rsa-enc.key').read_bytes()).hexdigest()};(p/'askpass-cases-3.json').write_text(json.dumps(result,indent=2)+'\n');assert all(r['expected_outcome_passed'] for r in runs)
