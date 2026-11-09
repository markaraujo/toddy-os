"""Continue unrun original protocol tests; preserve nonhermetic DNS failure."""
from pathlib import Path
import hashlib,json,re,subprocess
p=Path('/build');assert not (p/'remaining-results-2.json').exists() and not list(Path('/stage').iterdir())
def digest(f):
 with f.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
def artifacts():return {str(f.relative_to(p/'compile')):digest(f) for f in (p/'compile').rglob('*') if f.is_file() and not f.is_symlink() and f.open('rb').read(4)==b'\x7fELF'}
before=artifacts();assert before
old={}
for f in (p/'compile').rglob('*.trs'):
 m=re.search(r'^:test-result: (\S+)$',f.read_text(),re.M);assert m;old[str(f.relative_to(p/'compile'))]={'result':m[1],'sha256':digest(f),'log_sha256':digest(f.with_suffix('.log'))}
assert len(old)==303 and sum(r['result']=='PASS' for r in old.values())==269 and sum(r['result']=='SKIP' for r in old.values())==33
assert {name for name,r in old.items() if r['result']=='FAIL'}=={'src/gl/tests/test-getaddrinfo.trs'}
failure=(p/'compile/src/gl/tests/test-getaddrinfo.log').read_text();assert 'host=www.gnu.org' in failure and 'expected 0, got -2' in failure
(p/'initial-original-records-1.json').write_text(json.dumps(old,indent=2)+'\n');(p/'initial-ELFs-before-remaining-2.json').write_text(json.dumps(before,indent=2)+'\n')
runs=[]
# Root recursion already completed gl/lib/extra/po and src/gl; it stopped there.
# Only these later directories remain, never repeat the303 gnulib programs.
for directory in ['src','tests','fuzz']:
 with (p/('remaining-2-'+directory+'.log')).open('x') as log:r=subprocess.run(['make','-C','/build/compile/'+directory,'-j4','check'],stdout=log,stderr=subprocess.STDOUT)
 runs.append({'directory':directory,'exit':r.returncode});(p/'remaining-progress-2.json').write_text(json.dumps(runs,indent=2)+'\n')
 if r.returncode:raise SystemExit(r.returncode)
for name,row in old.items():assert digest(p/'compile'/name)==row['sha256'] and digest((p/'compile'/name).with_suffix('.log'))==row['log_sha256']
assert all(digest(p/'compile'/name)==sha for name,sha in before.items())
(p/'remaining-results-2.json').write_text(json.dumps({'scope':'Remaining original protocol/certificate suite only, initial269gnulib passes/33skips preserved. Nonhermetic public-DNS getaddrinfo remains FAILED/unqualified, not a pass or skip; native DNS/network gate pending','runs':runs,'initial_original_records':old,'initial_ELFs_unchanged':before,'new_tests_built_without_rebuilding_old_artifacts':True},indent=2)+'\n')
