"""Stage unchanged GnuTLS after selected original suites and real CA repair."""
from pathlib import Path
import hashlib,json,re,subprocess
p=Path('/build');assert not (p/'stage-results.json').exists() and not list(Path('/stage').iterdir())
def digest(f):
 with f.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
before={str(f.relative_to(p/'compile')):digest(f) for f in (p/'compile').rglob('*') if f.is_file() and not f.is_symlink() and f.open('rb').read(4)==b'\x7fELF'}
finished=json.loads((p/'certificate-results-3.json').read_text());assert all(r['exit']==0 for r in finished['runs'])
for name,sha in finished['prior_ELFs_unchanged'].items():assert before[name]==sha
for name,row in finished['prior_records_unchanged'].items():assert digest(p/'compile'/name)==row['sha256'] and digest((p/'compile'/name).with_suffix('.log'))==row['log_sha256']
tests=[]
for f in (p/'compile').rglob('*.trs'):
 m=re.search(r'^:test-result: (\S+)$',f.read_text(),re.M);assert m and m[1] in ['PASS','SKIP','FAIL'];tests.append({'name':str(f.relative_to(p/'compile')),'result':m[1]})
# Automake's certificate TESTS list repeats seven names: its summary counts
# 80 entries, but the actual driver emits only 73 distinct PASS records.
# Bind that discrepancy to retained output instead of inventing seven passes.
cert_log=(p/'certificates-3-tests-cert-tests.log').read_text()
listed=re.search(r'^make  (pathlen.sh .*?)$',cert_log,re.M)[1].split()
passed=re.findall(r'^PASS: (.+)$',cert_log,re.M)
assert len(listed)==80 and len(set(listed))==73
assert len(passed)==73 and set(passed)==set(listed)
assert {r['name'] for r in tests if r['name'].startswith('tests/cert-tests/')}=={'tests/cert-tests/'+n.removesuffix('.sh')+'.trs' for n in passed}
assert len(tests)==917 and sum(r['result']=='PASS' for r in tests)==813 and sum(r['result']=='SKIP' for r in tests)==102
assert {r['name'] for r in tests if r['result']=='FAIL'}=={'src/gl/tests/test-getaddrinfo.trs','tests/trust-store.trs'}
for name in ['tests/tls13/supported_versions.trs','tests/tls13/anti_replay.trs']:assert {'name':name,'result':'PASS'} in tests
# Native control-plane qualifier separately binds the staged-CA trust repair;
# this worker cannot read or fabricate installed-root acceptance receipts.
subprocess.run(['make','-C','/build/compile','DESTDIR=/stage','install'],check=True)
subprocess.run(['cc','/src/toddy-probe.c','-I/stage/usr/include','-L/stage/usr/lib','-lgnutls','-Wl,-rpath,/stage/usr/lib','-o','/build/native-probe'],check=True)
r=subprocess.run(['/build/native-probe'],capture_output=True,text=True,timeout=30);(p/'native-consumer.json').write_text(r.stdout);(p/'native-consumer.stderr').write_text(r.stderr);assert r.returncode==0
assert {name:digest(p/'compile'/name) for name in before}==before
result={'scope':'813distinct original standard passes/102skips reused, two original failures preserved. Default trust repaired in separate real CA stage; public DNS unqualified. Native crypto/default UTF8/IDNA/priority/refusal/recovery, not installed system trust/network/GNOME acceptance','compile_exit':0,'stage_exit':0,'original_tests':tests,'consumer':json.loads(r.stdout),'original_ELFs_unchanged':True,'artifacts':before,'stage_sha256':{str(f.relative_to(p/'stage')):digest(f) for f in (p/'stage').rglob('*') if f.is_file() and not f.is_symlink()}}
(p/'stage-results.json').write_text(json.dumps(result,indent=2)+'\n')
