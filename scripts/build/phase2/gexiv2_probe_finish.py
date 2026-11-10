"""Recover only own XMP language assertion after all original tests/build/stage0."""
from pathlib import Path
import hashlib,json,os,subprocess
w=Path('/build');assert os.getuid()==101
assert (w/'original-tests.exit').read_text().strip()=='0'
rows=[json.loads(x) for x in (w/'compile/meson-logs/testlog.json').read_text().splitlines() if x.strip()]
assert len(rows)==3 and all(r['result']=='OK' and r['returncode']==0 for r in rows)
def files(base,elf=False):
 return {str(p.relative_to(base)):hashlib.sha256(p.read_bytes()).hexdigest() for p in base.rglob('*') if p.is_file() and not p.is_symlink() and (not elf or p.open('rb').read(4)==b'\x7fELF')}
before=files(w/'compile',True);stage=files(w/'stage');assert before and stage and not (w/'consumer-2').exists() and not (w/'stage-results.json').exists()
probe=Path('/src/toddy-probe.py').read_text();old="r.try_get_tag_string(key)==value";new="r.try_get_tag_string(key)=='lang=\"x-default\" '+value";assert probe.count(old)==1;probe=probe.replace(old,new)
env=dict(os.environ,GI_TYPELIB_PATH='/stage/usr/lib/girepository-1.0',LD_LIBRARY_PATH='/stage/usr/lib')
with (w/'native-consumer-2.log').open('xb') as log:
 r=subprocess.run(['python3','-c',probe,'/build/consumer-2'],env=env,stdout=log,stderr=subprocess.PIPE)
(w/'native-consumer-2.stderr').write_bytes(r.stderr);(w/'native-consumer-2.exit').write_text(str(r.returncode)+'\n');assert r.returncode==0,r.stderr.decode()
consumer=json.loads((w/'native-consumer-2.log').read_text());assert files(w/'compile',True)==before and files(w/'stage')==stage
result={'scope':'Frozen GExiv20.16.2 C++ shared API/GI/Vala/Python/tools; all3 original C/Python programs0 reused unchanged, own corrected exact XMP language-tagged title readback/PNG reset/pixel retention/refusal/recovery. No original test/compiler/stage replay, no GUI acceptance.','compile_exit':0,'stage_exit':0,'original_tests':[{k:r[k] for k in ['name','result','returncode']} for r in rows],'consumer':consumer,'probe_sha256':hashlib.sha256(probe.encode()).hexdigest(),'artifacts':before,'stage_sha256':stage,'compile_and_stage_unchanged':True}
(w/'stage-results.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k not in ('artifacts','stage_sha256')}))
