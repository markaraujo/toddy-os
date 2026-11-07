#!/usr/bin/env python3
"""Check fresh mutable directories and native service access in a private guest."""
from pathlib import Path
import base64
import hashlib
import json
import os
import subprocess

os.chdir(Path(__file__).resolve().parents[2])
sources = {name: base64.b64encode(Path('scripts/build/h10/' + name + '.py').read_bytes()).decode()
           for name in ('live_accounts', 'root_inventory', 'fresh_directories', 'initramfs_runtime')}
baseline = json.loads(Path('config/live-account-baseline.json').read_text())
script = r'''from pathlib import Path
import base64,copy,hashlib,json,os,shutil,stat,subprocess,sys,tempfile,types
sys.path.insert(0,'/opt/toddy-build/scripts/build')
from package_backend import PackageBackend
root=Path('/mnt/lfs');backend=PackageBackend(root)
base=Path(tempfile.mkdtemp(prefix='toddy-fresh-directories-',dir=root/'tmp'))
print('FRESH_DIRECTORIES_FIXTURE '+str(base),flush=True)
for name,source in SOURCES.items():
 module=types.ModuleType(name);module.__file__='/opt/toddy-build/scripts/build/h10/'+name+'.py'
 sys.modules[name]=module;exec(compile(base64.b64decode(source),module.__file__,'exec'),module.__dict__)
helper=sys.modules['fresh_directories'];runtime=sys.modules['initramfs_runtime'];inventory=sys.modules['root_inventory']
baseline=BASELINE
before=inventory.digest(root/'var/lib/dpkg/status')
accounts_before={name:inventory.digest(root/'etc'/name) for name in ('passwd','group','shadow','gshadow')}
mounted=[]
try:
 rows=backend.run('dpkg-query','-W','-f=${Package}_${Version}_${Architecture}\t${Status}\n',capture_output=True,text=True).stdout
 records=[]
 for line in rows.splitlines():
  stem,state=line.split('\t');assert state=='install ok installed'
  records.append(json.loads((Path('/var/log/toddy/packages')/(stem+'.json')).read_text()))
 candidate=inventory.package_inventory(records)
 fresh=candidate['fresh_directories']
 assert 'var/cache' in fresh and 'var/log' in fresh
 assert not any(name=='var/cache' or name.startswith('var/cache/') or name=='var/log' or name.startswith('var/log/')
                for name in candidate['names'])
 source_metadata={name:{'mode':(root/name).stat().st_mode,'uid':(root/name).stat().st_uid,'gid':(root/name).stat().st_gid}
                  for name in fresh if (root/name).exists() and name.startswith(('var/cache','var/log'))}
 # Add package-time APT directory rows from its frozen CMake layout as a
 # component fixture. APT is not yet installed and is not counted accepted.
 fixture_plan=copy.deepcopy(fresh)
 for name in helper.APT_DIRECTORIES:
  fixture_plan.setdefault(name,{'mode':0o40755,'uid':0,'gid':0,'directory':True})
 template=base/'template'
 runtime.PROGRAMS=('/usr/bin/bash','/usr/bin/false','/usr/bin/id','/usr/sbin/chroot')
 runtime_report=runtime.stage_runtime(root,template,Path('/var/log/toddy/packages'))
 for name,device in (('null',(1,3)),('console',(5,1))):
  path=template/'dev'/name;info=path.lstat()
  assert stat.S_ISCHR(info.st_mode) and info.st_rdev==os.makedev(*device)
  path.unlink()
 for name in ('dev','proc','sys','run'):(template/name).rmdir()
 (template/'var/lib').mkdir(parents=True)
 # A copied parent with a default ACL must not leak builder access into newly
 # generated mutable children. Keep the original parent ACL unchanged.
 backend.run('setfacl','-m','d:u:101:rwx','/'+str((template/'var').relative_to(root)))
 parent_acl=os.getxattr(template/'var','system.posix_acl_default')
 def clone(name):
  image=base/name;shutil.copytree(template,image,symlinks=True);return image
 image=clone('image')
 report=helper.stage_directories(backend,image,fixture_plan,baseline)
 assert os.getxattr(image/'var','system.posix_acl_default')==parent_acl
 assert all(not os.listxattr(image/name) for name in report['directories'])
 sys.modules['live_accounts'].stage_accounts(image,baseline)
 prefix=['chroot',str(root),'/usr/sbin/chroot','--userspec=_apt:_apt','--groups=_apt','/'+str(image.relative_to(root))]
 env={'PATH':'/usr/bin:/usr/sbin','LC_ALL':'C','HOME':'/nonexistent'}
 identity=subprocess.run(prefix+['/usr/bin/id'],env=env,capture_output=True,text=True,check=True)
 assert identity.stdout.strip()=='uid=100(_apt) gid=100(_apt) groups=100(_apt)'
 access=[]
 for directory in ('var/cache/apt/archives/partial','var/lib/apt/lists/partial','var/lib/apt/lists/auxfiles'):
  write=subprocess.run(prefix+['/usr/bin/bash','--noprofile','--norc','-c','printf "public fixture\n" > "$1/probe"',
                               'probe','/'+directory],env=env,capture_output=True,text=True)
  assert write.returncode==0,(directory,write.stderr)
  file=image/directory/'probe';assert file.stat().st_uid==file.stat().st_gid==100
  foreign=['chroot',str(root),'/usr/sbin/chroot','--userspec=101:101','--groups=101','/'+str(image.relative_to(root))]
  denied=subprocess.run(foreign+['/usr/bin/bash','--noprofile','--norc','-c','test -w "$1"','probe','/'+directory],
                        env=env,capture_output=True,text=True)
  assert denied.returncode==1
  access.append({'directory':directory,'native_apt_write_exit':write.returncode,'foreign_uid_write_test_exit':denied.returncode})
  file.unlink()
 refused=[]
 for case in ('existing','redirect','missing-parent','unknown-uid','traversal','wrong-runtime-mode','filesystem-boundary'):
  target=clone(case);plan=copy.deepcopy(fixture_plan)
  if case=='existing':(target/'var/cache').mkdir();(target/'var/cache/keep').write_text('public retained fixture\n')
  elif case=='redirect':(target/'var/cache').symlink_to(base)
  elif case=='missing-parent':(target/'var/lib').rmdir()
  elif case=='unknown-uid':plan['var/cache']=dict(plan['var/cache'],uid=101)
  elif case=='traversal':plan['var/cache/../escape']=dict(plan['var/cache'])
  elif case=='wrong-runtime-mode':plan['tmp']=dict(plan['tmp'],mode=0o40777)
  else:
   subprocess.run(['mount','-t','tmpfs','-o','size=1m','tmpfs',str(target/'var/lib')],check=True)
   mounted.append(target/'var/lib')
  before_names=sorted(str(path.relative_to(target)) for path in target.rglob('*'))
  try:helper.stage_directories(backend,target,plan,baseline)
  except ValueError as error:refused.append({'case':case,'reason':str(error)})
  else:raise AssertionError('Unreviewed directory stage accepted: '+case)
  assert sorted(str(path.relative_to(target)) for path in target.rglob('*'))==before_names
  if case=='existing':assert (target/'var/cache/keep').read_text()=='public retained fixture\n'
  if mounted:subprocess.run(['umount',str(mounted.pop())],check=True)
 assert inventory.digest(root/'var/lib/dpkg/status')==before
 assert {name:inventory.digest(root/'etc'/name) for name in accounts_before}==accounts_before
 assert source_metadata=={name:{'mode':(root/name).stat().st_mode,'uid':(root/name).stat().st_uid,'gid':(root/name).stat().st_gid}
                          for name in source_metadata}
 print(json.dumps({'generation':report,'configured_package_records':len(records),'candidate_copy_paths':len(candidate['names']),
  'candidate_fresh_directories':len(fresh),'native_identity':identity.stdout.strip(),'access_checks':access,
  'negative_cases':refused,'parent_default_acl_unchanged':True,'new_directories_have_no_inherited_acl':True,
  'installed_database_accounts_and_source_directory_metadata_unchanged':True,
  'apt_namespace_is_prepared_source_layout_fixture':True,'actual_apt_acquisition_tested':False,
  'full_payload_preflight_or_boot_pass_claimed':False,'native_runtime':runtime_report,
  'source_sha256':{name:hashlib.sha256(base64.b64decode(source)).hexdigest() for name,source in SOURCES.items()},
  'fixture_removed_after_checks':True},indent=2))
except BaseException:
 print('Preserved fresh directories fixture: '+str(base),flush=True)
 raise
finally:
 for path in reversed(mounted):subprocess.run(['umount',str(path)],check=True)
shutil.rmtree(base)
'''.replace('SOURCES', repr(sources)).replace('BASELINE', repr(baseline))
result = subprocess.run(['python3', 'scripts/host/vm.py', 'ssh',
    'source /opt/toddy-build/scripts/build/target.sh; guard_target && unshare --mount --propagation private python3 -'],
    input=script, text=True, capture_output=True)
path = Path('.local/logs/h10-fresh-directories-probe.json')
data = (json.dumps({'exit': result.returncode, 'stdout': result.stdout, 'stderr': result.stderr}, indent=2) + '\n').encode()
sha = hashlib.sha256(data).hexdigest()
path.with_name(path.stem + '.' + sha + '.json').write_bytes(data)
path.write_bytes(data)
print(result.stdout, result.stderr)
print('exit', result.returncode, 'SHA256', sha)
result.check_returncode()
