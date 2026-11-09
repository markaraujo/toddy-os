from pathlib import Path
import hashlib,json,os,subprocess
p=Path('/build');assert not (p/'askpass-2.json').exists() and not (p/'initial-testlog-1.json').exists()
(p/'initial-testlog-1.json').write_bytes((p/'compile/meson-logs/testlog.json').read_bytes())
def artifacts():return {str(f.relative_to(p/'compile')):hashlib.sha256(f.read_bytes()).hexdigest() for f in (p/'compile').rglob('*') if f.is_file() and not f.is_symlink() and f.open('rb').read(4)==b'\x7fELF'}
before=artifacts();env=dict(os.environ,PATH='/build/test-sdk/bin:/usr/bin:/usr/sbin')
with (p/'askpass-2.log').open('x') as log:r=subprocess.run(['meson','test','-C','/build/compile','--no-rebuild','--print-errorlogs','--suite','gcr','ssh-askpass'],env=env,stdout=log,stderr=subprocess.STDOUT)
(p/'askpass-2.exit').write_text(str(r.returncode)+'\n');assert artifacts()==before
rows=[json.loads(s) for s in (p/'compile/meson-logs/testlog.json').read_text().splitlines() if s.strip()]
assert len(rows)==1
result={'exit':r.returncode,'original_programs':[{'name':x['name'],'result':x['result'],'returncode':x['returncode']} for x in rows],'unchanged_original_elfs':before,'private_source_sample_sha256':hashlib.sha256(Path('/src/gcr/fixtures/pem-rsa-enc.key').read_bytes()).hexdigest(),'private_source_sample_mode':Path('/src/gcr/fixtures/pem-rsa-enc.key').stat().st_mode&0o7777}
(p/'askpass-2.json').write_text(json.dumps(result,indent=2)+'\n');assert r.returncode==0 and rows[0]['result']=='OK' and rows[0]['returncode']==0
