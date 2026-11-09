"""Qualify staged Vala consumer with actual private code-generator search path."""
from pathlib import Path
import hashlib,json,os,re,subprocess
p=Path('/build');assert not (p/'stage-results.json').exists() and not (p/'consumer-2').exists()
assert not list((p/'consumer').iterdir())
def digest(f):
    with f.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
tests=[];records={}
for f in (p/'compile').rglob('*.trs'):
    m=re.search(r'^:test-result: (\S+)$',f.read_text(),re.M);assert m and m[1]=='PASS'
    name=str(f.relative_to(p/'compile'));tests.append({'name':name,'result':m[1]})
    records[name]={'trs':digest(f),'log':digest(f.with_suffix('.log'))}
assert len(tests)==1435
before={str(f.relative_to(p/'compile')):digest(f) for f in (p/'compile').rglob('*') if f.is_file() and not f.is_symlink() and f.open('rb').read(4)==b'\x7fELF'}
stage={str(f.relative_to(p/'stage')):digest(f) for f in (p/'stage').rglob('*') if f.is_file() and not f.is_symlink()}
assert 'usr/lib/vala-0.56/libvalaccodegen.so' in stage
(p/'ELFs-before-consumer-2.json').write_text(json.dumps(before,indent=2)+'\n')
(p/'original-records-before-consumer-2.json').write_text(json.dumps(records,indent=2)+'\n')
(p/'stage-before-consumer-2.json').write_text(json.dumps(stage,indent=2)+'\n')
env={**os.environ,'LD_LIBRARY_PATH':'/stage/usr/lib:/stage/usr/lib/vala-0.56'}
r=subprocess.run(['python3','/src/toddy-probe.py','/stage','/build/consumer-2'],env=env,capture_output=True,text=True,timeout=120)
(p/'native-consumer-2.json').write_text(r.stdout);(p/'native-consumer-2.stderr').write_text(r.stderr);assert r.returncode==0
for base,manifest in [('compile',before),('stage',stage)]:
    for name,sha in manifest.items():assert digest(p/base/name)==sha
for name,row in records.items():assert digest(p/'compile'/name)==row['trs'] and digest((p/'compile'/name).with_suffix('.log'))==row['log']
result={'scope':'1435original Vala programs and successful auxiliary make check retained; only own private staged-codegen discovery corrected. Actual generated native GObject/UTF8/signal/typed error and invalid-source/refusal/recovery; compiler SDK only, not IBus/native desktop acceptance.', 'compile_exit':0,'stage_exit':0,'original_tests':tests,'consumer':json.loads(r.stdout),'original_ELFs_and_stage_unchanged':True,'original_records_unchanged':True,'artifacts':before,'stage_sha256':stage}
(p/'stage-results.json').write_text(json.dumps(result,indent=2)+'\n')
