#!/usr/bin/env python3
"""Verify fresh native loader-cache generation and actual dynamic loading."""
from pathlib import Path
import base64
import hashlib
import json
import os
import subprocess

os.chdir(Path(__file__).resolve().parents[2])
sources = {name: base64.b64encode(Path('scripts/build/h10/' + name + '.py').read_bytes()).decode()
           for name in ('loader_cache', 'initramfs_runtime')}
script = r'''from pathlib import Path
import base64,hashlib,json,os,shutil,stat,subprocess,sys,tempfile,types
sys.path.insert(0,'/opt/toddy-build/scripts/build')
from package_backend import PackageBackend
root=Path('/mnt/lfs');backend=PackageBackend(root)
base=Path(tempfile.mkdtemp(prefix='toddy-loader-cache-',dir=root/'tmp'))
print('LOADER_CACHE_FIXTURE '+str(base),flush=True)
for name,source in SOURCES.items():
 module=types.ModuleType(name);module.__file__='/opt/toddy-build/scripts/build/h10/'+name+'.py'
 sys.modules[name]=module;exec(compile(base64.b64decode(source),module.__file__,'exec'),module.__dict__)
helper=sys.modules['loader_cache'];runtime=sys.modules['initramfs_runtime']
try:
 original_cache=helper.digest(root/'etc/ld.so.cache')
 original_aux=helper.digest(root/'var/cache/ldconfig/aux-cache')
 original_status=helper.digest(root/'var/lib/dpkg/status')
 rows=backend.run('dpkg-query','-W','-f=${Package}_${Version}_${Architecture}\t${Status}\n',capture_output=True,text=True).stdout
 entries={};providers={}
 for line in rows.splitlines():
  stem,state=line.split('\t');assert state=='install ok installed'
  record=json.loads((Path('/var/log/toddy/packages')/(stem+'.json')).read_text());assert record['installed']
  for path,row in record['payload'].items():
   if path in entries:assert row.get('directory') and entries[path]==row
   entries[path]=row;providers[path]={'name':record['name'],'version':record['version'],'archive_sha256':record['archive_sha256']}
 names={'/etc/ld.so.conf','/etc/ld.so.conf.d','/usr/sbin/ldconfig','/usr/bin/bash','/lib','/lib64','/var/cache','/usr/local/lib'}
 names.update(path for path in entries if path.startswith('/lib64/'))
 def add(virtual):
  names.add(virtual);path=root/virtual[1:]
  if path.is_symlink():
   link=path.readlink();target=link.as_posix() if link.is_absolute() else (Path(virtual).parent/link).as_posix()
   canonical='/' + str((root/target[1:]).resolve().relative_to(root))
   names.add(canonical)
 for virtual in runtime.runtime_dependencies(root,'/usr/bin/bash'):
  add('/'+runtime.destination_path(virtual))
 for virtual in list(names):
  for parent in Path(virtual).parents:
   if parent.as_posix()!='/':names.add(parent.as_posix())
 selected={name:entries[name] for name in names}
 template=base/'template';template.mkdir()
 for virtual in sorted(names,key=lambda name:(len(Path(name).parts),name)):
  source=root/virtual[1:];destination=template/virtual[1:];row=selected[virtual]
  source_stat=source.lstat();assert (source_stat.st_mode,source_stat.st_uid,source_stat.st_gid)==(row['mode'],row['uid'],row['gid'])
  if row.get('directory'):destination.mkdir(exist_ok=True);destination.chmod(stat.S_IMODE(row['mode']))
  elif 'sha256' in row:
   assert helper.digest(source)==row['sha256'];shutil.copy2(source,destination)
  else:assert source.readlink().as_posix()==row['symlink'];destination.symlink_to(row['symlink'])
 def inputs(image):
  result={}
  for virtual in selected:
   path=image/virtual[1:];st=path.lstat()
   result[virtual]={'mode':st.st_mode,'uid':st.st_uid,'gid':st.st_gid,
    'sha256':helper.digest(path) if stat.S_ISREG(st.st_mode) else None,
    'link':path.readlink().as_posix() if path.is_symlink() else None}
  return result
 def clone(name):
  image=base/name;shutil.copytree(template,image,symlinks=True);return image
 image=clone('image');before=inputs(image)
 first=helper.generate_loader_cache(backend,image,selected)
 assert inputs(image)==before
 dynamic=subprocess.run(['chroot',str(image),'/usr/bin/bash','--noprofile','--norc','-c',
  'export LD_DEBUG=libs; exec /usr/bin/bash --noprofile --norc -c \'printf "NATIVE_LOADER_OK\\n"\''],
  env={'PATH':'/usr/bin:/usr/sbin','LC_ALL':'C','HOME':'/root'},
  text=True,capture_output=True,timeout=30)
 assert dynamic.returncode==0 and dynamic.stdout=='NATIVE_LOADER_OK\n',(dynamic.returncode,dynamic.stdout,dynamic.stderr)
 assert 'search cache=/etc/ld.so.cache' in dynamic.stderr and 'calling init: /usr/lib/libc.so.6' in dynamic.stderr,dynamic.stderr
 assert '/lib/x86_64-linux-gnu' not in dynamic.stderr and 'initialize program: chroot' not in dynamic.stderr
 second_image=clone('second');second=helper.generate_loader_cache(backend,second_image,selected)
 assert first['sha256']==second['sha256']
 negatives=[]
 for case in ('existing-cache','partial-cache','inherited-auxiliary','redirected-auxiliary','changed-library',
              'changed-generator','unowned-library','changed-config','extra-config','tunables','redirected-library-dir','wrong-alias'):
  target=clone(case)
  if case=='existing-cache':(target/'etc/ld.so.cache').write_text('public inherited cache\n')
  elif case=='partial-cache':(target/'etc/ld.so.cache~').write_text('public interrupted cache\n')
  elif case=='inherited-auxiliary':
   path=target/'var/cache/ldconfig';path.mkdir(mode=0o700);(path/'aux-cache').write_text('public inherited auxiliary cache\n')
  elif case=='redirected-auxiliary':
   outside=base/'outside-aux';outside.mkdir();(target/'var/cache/ldconfig').symlink_to(outside)
  elif case=='changed-library':(target/'usr/lib/libc.so.6').write_bytes(b'public changed library\n')
  elif case=='changed-generator':(target/'usr/sbin/ldconfig').write_bytes(b'public changed generator\n')
  elif case=='unowned-library':(target/'usr/lib/libunowned.so.1').write_bytes(b'public unknown library\n')
  elif case=='changed-config':(target/'etc/ld.so.conf').write_text('/unreviewed\n')
  elif case=='extra-config':(target/'etc/ld.so.conf.d/unreviewed.conf').write_text('/unreviewed\n')
  elif case=='tunables':(target/'etc/tunables.conf').write_text('public unreviewed tunables\n')
  elif case=='redirected-library-dir':
   outside=base/'outside-libs';(target/'usr/lib').rename(outside);(target/'usr/lib').symlink_to(outside)
  else:(target/'lib').unlink();(target/'lib').symlink_to('unreviewed')
  old_cache=(target/'etc/ld.so.cache').read_bytes() if (target/'etc/ld.so.cache').exists() else None
  try:helper.generate_loader_cache(backend,target,selected)
  except ValueError as error:negatives.append({'case':case,'reason':str(error)})
  else:raise AssertionError('Unreviewed loader input accepted: '+case)
  assert ((target/'etc/ld.so.cache').read_bytes() if (target/'etc/ld.so.cache').exists() else None)==old_cache
  shutil.rmtree(target)
 assert helper.digest(root/'etc/ld.so.cache')==original_cache
 assert helper.digest(root/'var/cache/ldconfig/aux-cache')==original_aux
 assert helper.digest(root/'var/lib/dpkg/status')==original_status
 print(json.dumps({'first_generation':first,'second_sha256':second['sha256'],
  'two_generations_byte_identical':True,'native_dynamic_program':{'exit':dynamic.returncode,'stdout':dynamic.stdout,
  'loader_trace':dynamic.stderr},'negative_cases':negatives,'providers':{name:providers[name] for name in sorted(selected)},
  'installed_caches_and_package_database_unchanged':True,'fixture_removed_after_checks':True,
  'full_image_inventory_accepted':False,'native_boot_verified':False,
  'source_sha256':{name:hashlib.sha256(base64.b64decode(source)).hexdigest() for name,source in SOURCES.items()}},indent=2))
except BaseException:
 print('Preserved loader cache fixture: '+str(base),flush=True)
 raise
else:shutil.rmtree(base)
'''.replace('SOURCES', repr(sources))
result = subprocess.run(['python3', 'scripts/host/vm.py', 'ssh',
    'source /opt/toddy-build/scripts/build/target.sh; guard_target && python3 -'],
    input=script, text=True, capture_output=True)
path = Path('.local/logs/h10-loader-cache-probe.json')
data = (json.dumps({'exit': result.returncode, 'stdout': result.stdout, 'stderr': result.stderr}, indent=2) + '\n').encode()
sha = hashlib.sha256(data).hexdigest()
path.with_name(path.stem + '.' + sha + '.json').write_bytes(data)
path.write_bytes(data)
print(result.stdout, result.stderr)
print('exit', result.returncode, 'SHA256', sha)
result.check_returncode()
