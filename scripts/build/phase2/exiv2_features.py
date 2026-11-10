"""Resume compiled Exiv2 with real Brotli/INI inputs and complete private fixtures."""
from pathlib import Path
import hashlib,json,os,resource,signal,shutil,subprocess,time,sys
w=Path('/build');source=Path('/src');out=w/'features-3'
fs=os.statvfs(w);assert fs.f_bavail*fs.f_frsize>=16*1024**3+180*1024**2,'Target reserve and declared fixture/stage headroom required'
resource.setrlimit(resource.RLIMIT_CORE,(0,0));out.mkdir()
home=out/'home';home.mkdir();os.environ.update(HOME=str(home),XDG_CONFIG_HOME=str(home/'config'),XDG_CACHE_HOME=str(home/'cache'),XDG_DATA_HOME=str(home/'data'))
assert not list(Path('/stage').iterdir()) and not (w/'stage-results.json').exists()
old=json.loads((w/'original-results.json').read_text());assert [(r['name'],r['exit']) for r in old]==[('bugfixTests',1),('lensTests',1),('tiffTests',0),('versionTests',0),('regressionTests',0)]
def hashes(base,elf=False):
 return {str(p.relative_to(base)):hashlib.sha256(p.read_bytes()).hexdigest() for p in base.rglob('*') if p.is_file() and not p.is_symlink() and (not elf or p.open('rb').read(4)==b'ELF')}
legacy={'profile':'Brotli/INI disabled, no original pass claim for bugfix/lens; exact failed outputs retained','original_results':old,'ELFs':hashes(w/'compile',True),'CMakeCache_sha256':hashlib.sha256((w/'compile/CMakeCache.txt').read_bytes()).hexdigest()}
(out/'legacy-profile.json').write_text(json.dumps(legacy,indent=2)+chr(10))
for name in ['lib/libexiv2.so.0.28.8','bin/exiv2']:
 p=out/'legacy-binaries'/name;p.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(w/'compile'/name,p);assert hashlib.sha256(p.read_bytes()).hexdigest()==legacy['ELFs'][name]
for name in ['libbrotlidec','inih','INIReader']:
 value=subprocess.check_output(['pkg-config','--modversion',name],text=True).strip();assert value==('1.2.0' if name=='libbrotlidec' else '62')
def run(name,cmd,**kwargs):
 with (out/(name+'.log')).open('xb') as log:r=subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT,**kwargs)
 (out/(name+'.exit')).write_text(str(r.returncode)+chr(10));assert r.returncode==0,(name,r.returncode)
run('reconfigure',['cmake','-S','/src','-B','/build/compile','-DEXIV2_ENABLE_BROTLI=ON','-DEXIV2_ENABLE_INIH=ON'])
run('compile',['ninja','-C','/build/compile','-j4'])
private=out/'private-tests';private.mkdir();before={n:hashes(source/n) for n in ['test','tests']}
for name in before:shutil.copytree(source/name,private/name,symlinks=True);assert hashes(private/name)==before[name]
(private/'src').mkdir();(private/'src/canonmn_int.cpp').symlink_to('/src/src/canonmn_int.cpp');canon_before=hashlib.sha256((source/'src/canonmn_int.cpp').read_bytes()).hexdigest()
rows=json.loads((w/'original-registered-tests.json').read_text())['tests'];results=[]
for row in rows:
 command=row['command'];assert command[:3]==['/usr/bin/cmake','-E','env'] and 'EXIV2_BINDIR=/build/compile/bin' in command and command[5]=='runner.py' and next(p['value'] for p in row['properties'] if p['name']=='WORKING_DIRECTORY')=='/src/tests'
 began=time.monotonic();log=out/(row['name']+'.log')
 try:
  with log.open('xb') as stream:r=subprocess.run(command,cwd=private/'tests',stdout=stream,stderr=subprocess.STDOUT,timeout=480)
  result=r.returncode
 except subprocess.TimeoutExpired:result=None
 results.append({'name':row['name'],'exit':result,'seconds':round(time.monotonic()-began,3),'log_sha256':hashlib.sha256(log.read_bytes()).hexdigest()});(out/'original-results.json').write_text(json.dumps(results,indent=2)+chr(10))
 if result is None:break
assert before=={n:hashes(source/n) for n in before} and hashlib.sha256((source/'src/canonmn_int.cpp').read_bytes()).hexdigest()==canon_before
assert len(results)==5 and all(r['exit']==0 for r in results),'Preserve actual failed original tests, no promotion'
fs=os.statvfs(w);assert fs.f_bavail*fs.f_frsize>=16*1024**3+64*1024**2
run('stage',['cmake','--install','/build/compile'],env=dict(os.environ,DESTDIR='/stage'))
probe=sys.argv[1];(out/'probe.py').write_text(probe)
before_elf=hashes(w/'compile',True);before_stage=hashes(Path('/stage'))
with (out/'consumer.json').open('xb') as stream,(out/'consumer.stderr').open('xb') as error:r=subprocess.run(['python3',str(out/'probe.py'),'/stage/usr/bin/exiv2',str(out/'consumer')],env=dict(os.environ,LD_LIBRARY_PATH='/stage/usr/lib'),stdout=stream,stderr=error)
consumer_exit=r.returncode
assert before_elf==hashes(w/'compile',True) and before_stage==hashes(Path('/stage'))
r={'scope':'Frozen Exiv20.28.8 with real Brotli/INI dependencies, original five private drivers on new feature inputs; failed profile retained with original ELF copies. Network transports/samples/Python bindings omitted. Own PNG EXIF UTF8 edit/read/reset/pixel retention/corrupt refusal and XMP positive/external-entity denial/recovery only; no global XML vulnerability fix or GExiv2/LocalSearch/GUI acceptance.','compile_exit':0,'stage_exit':0,'original_tests':results,'legacy_profile':'features-3/legacy-profile.json','private_source_fixture_sha256':hashlib.sha256(json.dumps(before,sort_keys=True).encode()).hexdigest(),'readonly_canon_source_sha256':canon_before,'consumer_exit':consumer_exit,'consumer':json.loads((out/'consumer.json').read_text()) if consumer_exit==0 else None,'artifacts':hashes(w/'compile',True),'stage_sha256':hashes(Path('/stage'))}
(w/'stage-results.json').write_text(json.dumps(r,indent=2)+chr(10));print(json.dumps({k:v for k,v in r.items() if k not in ('artifacts','stage_sha256')}))

assert consumer_exit==0, "Own consumer failure retained with successful compilation/original/stage manifests; do not replay them"
