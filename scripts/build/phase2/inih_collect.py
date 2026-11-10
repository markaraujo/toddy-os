from pathlib import Path
import hashlib,json
w=Path('/build');assert not (w/'stage-results.json').exists() and (w/'original-tests.exit').read_text().strip()=='0'
rows=[json.loads(x) for x in (w/'compile/meson-logs/testlog.json').read_text().splitlines() if x.strip()];assert len(rows)==16 and all(r['result']=='OK' and r['returncode']==0 for r in rows)
r={'scope':'Frozen inih62 C+INIReader C++ shared libraries/default bounded stack parser; all16original Meson programs and own C/C++ UTF8/typed-default/refusal/state-retention/recovery. No Exiv2/user-owned config or GUI acceptance.','compile_exit':0,'stage_exit':0,'original_tests':[{k:r[k] for k in ['name','result','returncode']} for r in rows],'consumer':json.loads((w/'native-consumer.json').read_text()),'artifacts':{str(p.relative_to(w/'compile')):hashlib.sha256(p.read_bytes()).hexdigest() for p in (w/'compile').rglob('*') if p.is_file() and not p.is_symlink() and p.open('rb').read(4)==b'\x7fELF'},'stage_sha256':{str(p.relative_to('/stage')):hashlib.sha256(p.read_bytes()).hexdigest() for p in Path('/stage').rglob('*') if p.is_file() and not p.is_symlink()}}
(w/'stage-results.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({k:v for k,v in r.items() if k not in ('artifacts','stage_sha256')}))
assert len(r['original_tests'])==len(json.loads((w/'original-registered-tests.json').read_text()))==16
