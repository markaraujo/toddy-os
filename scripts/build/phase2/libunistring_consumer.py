"""Use documented UTF8 validation before normalizing; preserve full original suite."""
from pathlib import Path
import hashlib,json,re,subprocess,sys
p=Path('/build');assert not (p/'stage-results.json').exists() and not (p/'native-probe-2').exists()
def digest(f):
 with f.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
artifacts={str(f.relative_to(p/'compile')):digest(f) for f in (p/'compile').rglob('*') if f.is_file() and not f.is_symlink() and f.open('rb').read(4)==b'\x7fELF'}
stage={str(f.relative_to(p/'stage')):digest(f) for f in (p/'stage').rglob('*') if f.is_file() and not f.is_symlink()}
tests=[]
for f in (p/'compile').rglob('*.trs'):
 m=re.search(r'^:test-result: (\S+)$',f.read_text(),re.M);assert m and m[1] in ['PASS','SKIP'];tests.append({'name':str(f.relative_to(p/'compile')),'result':m[1]})
assert len(tests)==674 and sum(r['result']=='PASS' for r in tests)==638
source=p/'native-probe-2.c';source.write_text(sys.argv[1]);assert 'u8_normalize(UNINORM_NFC,invalid' not in source.read_text()
subprocess.run(['cc',str(source),'-I/stage/usr/include','-L/stage/usr/lib','-lunistring','-Wl,-rpath,/stage/usr/lib','-o','/build/native-probe-2'],check=True)
r=subprocess.run(['/build/native-probe-2'],capture_output=True,text=True,timeout=20);(p/'native-consumer-2.json').write_text(r.stdout);(p/'native-consumer-2.stderr').write_text(r.stderr);assert r.returncode==0
assert {name:digest(p/'compile'/name) for name in artifacts}==artifacts and {name:digest(p/'stage'/name) for name in stage}==stage
result={'scope':'Original638Unicode passes/36original skips reused; native validation/NFC/Portuguese case/state/lifecycle. Own initial normalizer-refusal assumption superseded: malformed input is rejected by u8_check, not passed to unchecked normalizer. No GnuTLS/TLS/network acceptance','compile_exit':0,'stage_exit':0,'original_tests':tests,'consumer':json.loads(r.stdout),'consumer_source_sha256':digest(source),'consumer_binary_sha256':digest(p/'native-probe-2'),'original_ELFs_unchanged':True,'stage_unchanged':True,'artifacts':artifacts,'stage_sha256':stage}
(p/'stage-results.json').write_text(json.dumps(result,indent=2)+'\n')
