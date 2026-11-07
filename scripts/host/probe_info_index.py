#!/usr/bin/env python3
"""Exercise fresh Info generation using actual native documents and programs."""
from pathlib import Path
import base64
import hashlib
import json
import os
import subprocess

os.chdir(Path(__file__).resolve().parents[2])
sources = {name: base64.b64encode(Path('scripts/build/h10/' + name + '.py').read_bytes()).decode()
           for name in ('info_index', 'initramfs_runtime')}
script = r'''from pathlib import Path
import base64,hashlib,json,os,shutil,subprocess,sys,tempfile,types
sys.path.insert(0,'/opt/toddy-build/scripts/build')
from package_backend import PackageBackend
root=Path('/mnt/lfs');backend=PackageBackend(root)
base=Path(tempfile.mkdtemp(prefix='toddy-info-index-',dir=root/'tmp'))
print('INFO_INDEX_FIXTURE '+str(base),flush=True)
for name,source in SOURCES.items():
 module=types.ModuleType(name);module.__file__='/opt/toddy-build/scripts/build/h10/'+name+'.py'
 sys.modules[name]=module;exec(compile(base64.b64decode(source),module.__file__,'exec'),module.__dict__)
runtime=sys.modules['initramfs_runtime'];helper=sys.modules['info_index']
try:
 source_index_sha=helper.digest(root/'usr/share/info/dir')
 status_sha=helper.digest(root/'var/lib/dpkg/status')
 rows=backend.run('dpkg-query','-W','-f=${Package}_${Version}_${Architecture}\t${Status}\n',capture_output=True,text=True).stdout
 selected={};providers={};original_index_owners=[]
 for line in rows.splitlines():
  stem,state=line.split('\t');assert state=='install ok installed'
  record=json.loads((Path('/var/log/toddy/packages')/(stem+'.json')).read_text())
  assert record['installed']
  for path,row in record['payload'].items():
   if path=='/usr/share/info/dir':original_index_owners.append(record['name']);continue
   if not (path.startswith('/usr/share/info/') or path in ('/usr/bin/install-info','/usr/bin/info')):continue
   assert path not in selected or row.get('directory') and selected[path]==row
   selected[path]=row;providers[path]={'name':record['name'],'version':record['version'],'archive_sha256':record['archive_sha256']}
 # This private component scope intentionally omits the existing shared source
 # index; it does not bypass the full inventory's H07 metadata-closure refusal.
 runtime.PROGRAMS=('/usr/bin/bash','/usr/bin/install-info','/usr/bin/info')
 image=base/'image';runtime_report=runtime.stage_runtime(root,image,Path('/var/log/toddy/packages'))
 for virtual,row in sorted(selected.items()):
  source=root/virtual[1:];destination=image/virtual[1:]
  assert source.parent.resolve()==source.parent
  metadata=source.lstat();assert (metadata.st_mode,metadata.st_uid,metadata.st_gid)==(row['mode'],row['uid'],row['gid'])
  if row.get('directory'):destination.mkdir(parents=True,exist_ok=True);continue
  assert source.is_file() and not source.is_symlink() and helper.digest(source)==row['sha256']
  destination.parent.mkdir(parents=True,exist_ok=True)
  if not destination.exists():shutil.copy2(source,destination)
 null=image/'dev/null';assert null.stat().st_rdev==os.makedev(1,3);null.unlink()
 first=helper.generate_info_index(backend,image,selected)
 assert first['transient_null_created_and_removed'] and not null.exists()
 data=(image/'usr/share/info/dir').read_bytes()
 with helper.temporary_null(image):
  readers={}
  for manual in ('libc','coreutils','bash','texinfo'):
   args=['chroot',str(image),'/usr/bin/info','--directory=/usr/share/info','--where',manual]
   result=subprocess.run(args,env={'PATH':'/usr/bin:/usr/sbin','LC_ALL':'C','HOME':'/root'},text=True,capture_output=True,timeout=30)
   assert result.returncode==0,(manual,result.stdout,result.stderr)
   assert result.stdout.strip()=='/usr/share/info/'+manual+'.info',result.stdout
   node=subprocess.run(['chroot',str(image),'/usr/bin/info','--directory=/usr/share/info',
    '--output=-','--node=Top',manual],env={'PATH':'/usr/bin:/usr/sbin','LC_ALL':'C','HOME':'/root'},capture_output=True,timeout=30)
   assert node.returncode==0 and len(node.stdout)>100,(manual,node.returncode,node.stderr)
   readers[manual]={'where':result.stdout.strip(),'exit':node.returncode,'bytes':len(node.stdout),
    'sha256':hashlib.sha256(node.stdout).hexdigest()}
  # Traverse actual generated menu entries whose labels differ from filenames.
  menu_readers={}
  for menu in ('Bash','Coreutils'):
   result=subprocess.run(['chroot',str(image),'/usr/bin/info','--directory=/usr/share/info',
    '--file=dir','--output=-',menu],env={'PATH':'/usr/bin:/usr/sbin','LC_ALL':'C','HOME':'/root'},
    capture_output=True,timeout=30)
   assert result.returncode==0 and len(result.stdout)>100,(menu,result.returncode,result.stderr)
   assert hashlib.sha256(result.stdout).hexdigest()==readers[menu.lower()]['sha256']
   menu_readers[menu]={'exit':result.returncode,'resolved_document_matches':menu.lower()}
 negatives=[]
 assert not null.exists()
 try:
  with helper.temporary_null(image):
   assert null.stat().st_rdev==os.makedev(1,3)
   raise RuntimeError('controlled null cleanup failure')
 except RuntimeError as error:assert str(error)=='controlled null cleanup failure'
 assert not null.exists()
 for kind in ('regular','redirected'):
  if kind=='regular':null.write_text('preserve unexpected device input\n')
  else:null.symlink_to(base/'outside-device')
  try:
   with helper.temporary_null(image):raise AssertionError('Unexpected null accepted')
  except ValueError as error:negatives.append({'case':kind+' null device','reason':str(error)})
  assert null.exists() or null.is_symlink()
  null.unlink()
 def refuse(case,entries):
  before={str(path.relative_to(image/'usr/share/info')):helper.digest(path)
   for path in (image/'usr/share/info').rglob('*') if path.is_file()}
  try:helper.generate_info_index(backend,image,entries)
  except ValueError as error:negatives.append({'case':case,'reason':str(error)})
  else:raise AssertionError('Unexpected Info acceptance: '+case)
  assert before=={str(path.relative_to(image/'usr/share/info')):helper.digest(path)
   for path in (image/'usr/share/info').rglob('*') if path.is_file()}
 refuse('existing-index',selected)
 (image/'usr/share/info/dir').unlink()
 refuse('owned-shared-index',{**selected,'/usr/share/info/dir':{'sha256':source_index_sha}})
 extra=image/'usr/share/info/unowned.info';extra.write_text('public extra fixture\n');refuse('unowned-document',selected);extra.unlink()
 manual=image/'usr/share/info/libc.info';original=manual.read_bytes();manual.write_bytes(b'public changed manual\n')
 refuse('changed-document',selected);manual.write_bytes(original)
 executable=image/'usr/bin/install-info';original=executable.read_bytes();executable.write_bytes(b'public changed generator\n')
 refuse('changed-generator',selected);executable.write_bytes(original)
 manual=image/'usr/share/info/libc.info';outside=base/'outside-manual';manual.rename(outside);manual.symlink_to(outside)
 refuse('redirected-document',selected);manual.unlink();outside.rename(manual)
 directory=image/'usr/share/info';outside=base/'outside-info';directory.rename(outside);directory.symlink_to(outside)
 refuse('redirected-directory',selected);directory.unlink();outside.rename(directory)
 partial=directory/'dir-interrupted';partial.write_text('public interrupted index\n');refuse('partial-index-output',selected);partial.unlink()
 second=helper.generate_info_index(backend,image,selected)
 assert (directory/'dir').read_bytes()==data
 assert second['transient_null_created_and_removed'] and not null.exists()
 assert helper.digest(root/'usr/share/info/dir')==source_index_sha and helper.digest(root/'var/lib/dpkg/status')==status_sha
 report={'first_generation':first,'second_sha256':second['sha256'],'two_generations_byte_identical':True,
  'native_readers':readers,'native_menu_readers':menu_readers,'negative_cases':negatives,'document_providers':sorted({row['name'] for row in providers.values()}),
  'providers':providers,'runtime':runtime_report,'source_index_owners_still_pending_metadata_closure':original_index_owners,
  'installed_index_and_package_database_unchanged':True,'fixture_removed_after_checks':True,
  'full_image_inventory_accepted':False,'native_boot_verified':False,
  'source_sha256':{name:hashlib.sha256(base64.b64decode(source)).hexdigest() for name,source in SOURCES.items()}}
 print(json.dumps(report,indent=2))
except BaseException:
 print('Preserved Info fixture: '+str(base),flush=True)
 raise
else:shutil.rmtree(base)
'''.replace('SOURCES', repr(sources))
result = subprocess.run(['python3', 'scripts/host/vm.py', 'ssh',
    'source /opt/toddy-build/scripts/build/target.sh; guard_target && python3 -'],
    input=script, text=True, capture_output=True)
path = Path('.local/logs/h10-info-index-probe.json')
data = (json.dumps({'exit': result.returncode, 'stdout': result.stdout, 'stderr': result.stderr}, indent=2) + '\n').encode()
sha = hashlib.sha256(data).hexdigest()
path.with_name(path.stem + '.' + sha + '.json').write_bytes(data)
path.write_bytes(data)
print(result.stdout, result.stderr)
print('exit', result.returncode, 'SHA256', sha)
result.check_returncode()
