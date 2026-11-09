"""Finish only own Nettle4 digest API consumer; all original crypto evidence reused."""
from pathlib import Path
import hashlib,json,re,subprocess,sys
p=Path('/build');assert not (p/'stage-results.json').exists() and not (p/'native-probe-2').exists()
def digest(f):
 with f.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
artifacts={str(f.relative_to(p/'compile')):digest(f) for f in (p/'compile').rglob('*') if f.is_file() and not f.is_symlink() and f.open('rb').read(4)==b'\x7fELF'}
stage={str(f.relative_to(p/'stage')):digest(f) for f in (p/'stage').rglob('*') if f.is_file() and not f.is_symlink()}
text=(p/'original-tests.log').read_text();tests=[{'name':m[2],'result':m[1]} for m in re.finditer(r'^(PASS|SKIP|FAIL): (.+)$',text,re.M)]
assert len(tests)==123 and sum(r['result']=='PASS' for r in tests)==122 and [r for r in tests if r['result']!='PASS']==[{'name':'x86-ibt','result':'SKIP'}]
assert 'tests failed' not in text and len(re.findall(r'^All \d+ tests passed$',text,re.M))==3
source=p/'native-probe-2.c';source.write_text(sys.argv[1]);assert 'sha256_digest(&hash,output)' in source.read_text()
subprocess.run(['cc',str(source),'-I/stage/usr/include','-L/stage/usr/lib','-lhogweed','-lnettle','-lgmp','-Wl,-rpath,/stage/usr/lib','-o','/build/native-probe-2'],check=True)
r=subprocess.run(['/build/native-probe-2'],capture_output=True,text=True,timeout=20);(p/'native-consumer-2.json').write_text(r.stdout);(p/'native-consumer-2.stderr').write_text(r.stderr);assert r.returncode==0
assert {name:digest(p/'compile'/name) for name in artifacts}==artifacts and {name:digest(p/'stage'/name) for name in stage}==stage
result={'scope':'122original crypto program passes and1upstream CET/IBT skip; own fixed Nettle4 two-argument digest API consumer, not TLS/GnuTLS/remote network acceptance','compile_exit':0,'stage_exit':0,'original_tests':tests,'consumer':json.loads(r.stdout),'consumer_source_sha256':digest(source),'consumer_binary_sha256':digest(p/'native-probe-2'),'original_ELFs_unchanged':True,'stage_unchanged':True,'artifacts':artifacts,'stage_sha256':stage}
(p/'stage-results.json').write_text(json.dumps(result,indent=2)+'\n')
