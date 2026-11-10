from pathlib import Path
import hashlib,json,os,shutil,subprocess,time
w=Path('/build');source=Path('/src');private=w/'private-tests';assert private.is_dir() and not (w/'original-results.json').exists()
def hashes(root):return {str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in root.rglob('*') if p.is_file() and not p.is_symlink()}
before={n:hashes(source/n) for n in ['test','tests']}
elfs_before={str(p.relative_to(w/'compile')):hashlib.sha256(p.read_bytes()).hexdigest() for p in (w/'compile').rglob('*') if p.is_file() and not p.is_symlink() and p.open('rb').read(4)==b'\x7fELF'}
for name in ['test','tests']:assert hashes(private/name)==before[name]
registered=json.loads((w/'original-registered-tests.json').read_text());rows=registered['tests'];assert {r['name'] for r in rows}=={'bugfixTests','lensTests','tiffTests','versionTests','regressionTests'}
results=[]
for row in rows:
 command=row['command'];assert command[:3]==['/usr/bin/cmake','-E','env'] and 'EXIV2_BINDIR=/build/compile/bin' in command and command[5]=='runner.py' and next(p['value'] for p in row['properties'] if p['name']=='WORKING_DIRECTORY')=='/src/tests'
 cmd=list(command);log=w/(row['name']+'.log');began=time.monotonic()
 try:
  with log.open('xb') as out:r=subprocess.run(cmd,cwd=private/'tests',stdout=out,stderr=subprocess.STDOUT,timeout=480)
  exit=r.returncode
 except subprocess.TimeoutExpired:exit=None
 results.append({'name':row['name'],'exit':exit,'seconds':round(time.monotonic()-began,3),'log_sha256':hashlib.sha256(log.read_bytes()).hexdigest()})
 (w/'original-results.json').write_text(json.dumps(results,indent=2)+'\n')
 if exit is None:break
assert before=={n:hashes(source/n) for n in before}
(w/'original-private-fixtures.json').write_text(json.dumps({'scope':'Unmodified original drivers on byte-identical private test/data copy, source immutable; only outputs under private fixture/test/tmp','input_files':sum(len(r) for r in before.values()),'source_before_after_manifest_sha256':hashlib.sha256(json.dumps(before,sort_keys=True).encode()).hexdigest()},indent=2)+'\n')
assert len(results)==5 and all(r['exit']==0 for r in results),'Retain actual original failures/timeouts; no promotion'
subprocess.run(['cmake','--install','/build/compile'],env=dict(os.environ,DESTDIR='/stage'),check=True)
with (w/'native-consumer.json').open('xb') as output:r=subprocess.run(['python3','/src/toddy-probe.py','/stage/usr/bin/exiv2','/build/consumer'],env=dict(os.environ,LD_LIBRARY_PATH='/stage/usr/lib'),stdout=output)
assert r.returncode==0
assert elfs_before=={str(p.relative_to(w/'compile')):hashlib.sha256(p.read_bytes()).hexdigest() for p in (w/'compile').rglob('*') if p.is_file() and not p.is_symlink() and p.open('rb').read(4)==b'\x7fELF'}
from pathlib import Path
import hashlib,json
w=Path('/build');r={'scope':'Frozen Exiv2 local PNG/JPEG/TIFF/BMFF/video/XMP metadata profile; supported optional Brotli/INI and upstream-default network transports omitted. Original five private CTest drivers, raw nested skips/outcomes retained, own local metadata/refusal/reset only; no GExiv2/LocalSearch/GUI acceptance.','compile_exit':0,'stage_exit':0,'original_tests':json.loads((w/'original-results.json').read_text()),'consumer':json.loads((w/'native-consumer.json').read_text()),'artifacts':{str(p.relative_to(w/'compile')):hashlib.sha256(p.read_bytes()).hexdigest() for p in (w/'compile').rglob('*') if p.is_file() and not p.is_symlink() and p.open('rb').read(4)==b'\x7fELF'},'stage_sha256':{str(p.relative_to('/stage')):hashlib.sha256(p.read_bytes()).hexdigest() for p in Path('/stage').rglob('*') if p.is_file() and not p.is_symlink()}}
(w/'stage-results.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({k:v for k,v in r.items() if k not in ('artifacts','stage_sha256')}))
