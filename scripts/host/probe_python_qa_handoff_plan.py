#!/usr/bin/env python3
"""Read-only installed provenance check for a private Python QA archive plan."""
from pathlib import Path
import base64
import hashlib
import json
import os
import subprocess

os.chdir(Path(__file__).resolve().parents[2])
sources = {name: base64.b64encode((Path('scripts/build') / name).read_bytes()).decode()
           for name in ('h11/python_qa.py', 'python_qa_handoff.py', 'stage_package.py')}
script = r'''from pathlib import Path
import base64,hashlib,json,re,shutil,sys,tempfile,types
sys.path.insert(0,'/opt/toddy-build/scripts/build')
from package_backend import PackageBackend
root=Path('/mnt/lfs');backend=PackageBackend(root)
base=Path(tempfile.mkdtemp(prefix='toddy-python-qa-handoff-',dir=root/'tmp'))
print('PYTHON_QA_HANDOFF_FIXTURE '+str(base),flush=True)
for name,body in SOURCES.items():
 path=base/'scripts/build'/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(base64.b64decode(body))
modules={}
for name,body in SOURCES.items():
 key=name.removesuffix('.py').replace('/','_')
 module=types.ModuleType(key);module.__file__=str(base/'scripts/build'/name)
 sys.modules[key]=module;exec(compile(base64.b64decode(body),module.__file__,'exec'),module.__dict__)
 modules[name]=module
def digest(path):
 with path.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
version,arch,status=backend.run('dpkg-query','-W','-f=${Version}\t${Architecture}\t${Status}','python',capture_output=True,text=True).stdout.split('\t')
assert status=='install ok installed'
record=json.loads((Path('/var/log/toddy/packages')/f'python_{version}_{arch}.json').read_text())
archive=Path('/var/cache/toddy/packages')/f'python_{version}_{arch}.deb'
assert digest(archive)==record['archive_sha256']
before=digest(root/'var/lib/dpkg/status')
try:
 copied=base/'source.deb';shutil.copyfile(archive,copied)
 runtime=base/'runtime';qa=base/'qa'
 backend.run('dpkg-deb','--extract','/'+str(copied.relative_to(root)),'/'+str(runtime.relative_to(root)))
 modules['h11/python_qa.py'].partition(runtime,qa)
 notice=qa/'usr/share/doc/python-test-support/copyright';notice.parent.mkdir(parents=True)
 shutil.copy2(runtime/'usr/share/doc/python/copyright',notice)
 entries=modules['stage_package.py'].payload(qa)
 ownership={}
 for listing in (root/'var/lib/dpkg/info').glob('*.list'):
  for path in listing.read_text().splitlines():ownership.setdefault(path.rstrip('/'),set()).add(listing.stem)
 revision=re.search(r'\+toddy([1-9][0-9]*)$',version)
 successor=(version[:revision.start()]+'+toddy'+str(int(revision[1])+1)) if revision else version+'+toddy1'
 args=types.SimpleNamespace(name='python-test-support',version=successor,architecture=arch,
  depends=modules['python_qa_handoff.py'].qa_dependencies(successor),source=[r['filename'] for r in record['sources']],install=False)
 def prepare():return modules['python_qa_handoff.py'].prepare(backend,root,Path('/var/cache/toddy/packages'),Path('/var/log/toddy/packages'),modules['stage_package.py'].payload(qa),ownership,qa,args)
 plan=prepare();assert plan['transferred_path_count']==5395 and not plan['installation_authorized']
 rejected=[]
 complete_dependencies=args.depends;args.depends=f'python (= {successor})'
 try:prepare()
 except ValueError as error:rejected.append({'case':'missing direct interpreter providers','reason':str(error)})
 else:raise AssertionError('Incomplete direct dependencies accepted')
 args.depends=complete_dependencies
 args.install=True
 try:prepare()
 except ValueError as error:rejected.append({'case':'install flag','reason':str(error)})
 else:raise AssertionError('Install flag accepted')
 args.install=False
 selected=next(path for path in plan['transferred_paths'] if path.endswith('.py'))
 path=qa/selected.lstrip('/');original=path.read_bytes();mtime=path.stat().st_mtime_ns
 path.write_bytes(original+b'\n# private altered fixture\n')
 try:prepare()
 except ValueError as error:rejected.append({'case':'changed staged bytes','reason':str(error)})
 else:raise AssertionError('Changed QA accepted')
 path.write_bytes(original);import os;os.utime(path,ns=(mtime,mtime))
 assert prepare()==plan
 assert digest(root/'var/lib/dpkg/status')==before
 print(json.dumps({'plan':plan,'negative_cases':rejected,'restored_staging_accepted':True,
  'actual_installed_bytes_modes_owners_timestamps_checked':True,
  'installed_status_unchanged':True,'native_package_cache_changed':False,'production_cli_dispatched':False,
  'source_sha256':{name:hashlib.sha256(base64.b64decode(body)).hexdigest() for name,body in SOURCES.items()},
  'fixture_removed_after_checks':True},indent=2))
except BaseException:
 print('Preserved Python QA handoff fixture:',base,flush=True)
 raise
else:shutil.rmtree(base)
'''.replace('SOURCES', repr(sources))
r = subprocess.run(['python3', 'scripts/host/vm.py', 'ssh',
                    'source /opt/toddy-build/scripts/build/target.sh; guard_target && python3 -'],
                   input=script, text=True, capture_output=True)
p = Path('.local/logs/h11-python-qa-handoff-plan-probe.json')
data = (json.dumps({'exit': r.returncode, 'stdout': r.stdout, 'stderr': r.stderr}, indent=2) + '\n').encode()
sha = hashlib.sha256(data).hexdigest()
p.with_name(p.stem + '.' + sha + '.json').write_bytes(data)
p.write_bytes(data)
print(r.stdout, r.stderr)
print('exit', r.returncode, 'SHA256', sha)
r.check_returncode()
